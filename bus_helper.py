import requests
import geopy.distance
import pandas as pd
import geopandas as gpd
from datetime import datetime, timedelta, timezone

def convert_to_longlat(shp_file):
    # Reproject the GeoDataFrame to the target CRS (convert x and y to long and lat)
    gdf = gpd.read_file(shp_file)
    target_crs = 'EPSG:4326'
    gdf = gdf.to_crs(target_crs)
    gdf['latitude'] = gdf.geometry.y
    gdf['longitude'] = gdf.geometry.x
    return gdf

def get_all_bus_arrival_from_bus_stop(bus_stop_no, lta_api_key):
    url = "http://datamall2.mytransport.sg/ltaodataservice/BusArrivalv2?BusStopCode={}".format(str(bus_stop_no))
    headers = {'AccountKey': lta_api_key}
    response = requests.get(url, headers=headers)
    data = response.json()
    current_time = datetime.now(timezone.utc)
    result = []
    for bus in data['Services']:
        arrival_timing = []
        for nb in ['NextBus','NextBus2','NextBus3']:
            time_value = get_time_differences(current_time,bus[nb]['EstimatedArrival'])
            if time_value:
                arrival_timing.append(time_value[0])
        bus_dict = {'service' : bus['ServiceNo'], 'arrival' : arrival_timing}
        result.append(bus_dict)
    return result

def get_specific_bus_arrival_from_bus_stop(bus_stop_no, lta_api_key, bus_svc):
    url = "http://datamall2.mytransport.sg/ltaodataservice/BusArrivalv2?BusStopCode={}".format(str(bus_stop_no))
    headers = {'AccountKey': lta_api_key}
    response = requests.get(url, headers=headers)
    data = response.json()
    current_time = datetime.now(timezone.utc)
    result = []
    for bus in data['Services']:
        if bus['ServiceNo'] == bus_svc:
            arrival_timing = []
            for nb in ['NextBus','NextBus2','NextBus3']:
                time_value = get_time_differences(current_time,bus[nb]['EstimatedArrival'])
                if time_value:
                    arrival_timing.append(time_value[0])
            bus_dict = {'service' : bus['ServiceNo'], 'arrival' : arrival_timing}
            result.append(bus_dict)
    return result

def convert_to_message(bus_stop_df, bus_stop_no, result):
    bus_stop_details = get_bus_stop_details(bus_stop_df, bus_stop_no)
    if bus_stop_details == "No such Bus Stop!":
        return "No such Bus Stop!"
    header = "Bus Stop: {}, Bus Stop No: {}  \n\n".format(bus_stop_details[0],str(bus_stop_no))
    full_msg = header
    for index in range(len(result)):
        bus = result[index]
        arrival1 = str(bus['arrival'][0])
        arrival2 = str(bus['arrival'][1])
        arrival3 = str(bus['arrival'][2])
        if arrival1 == '99999' and arrival2 == '99999' and arrival3 == '99999':
            bus_msg = "{}'s info not available now.  \n"
        elif arrival1 != '99999' and arrival2 == '99999' and arrival3 == '99999':
            bus_msg = "{} is arriving in {} mins.  \n".format(bus['service'], arrival1)
        elif arrival1 != '99999' and arrival2 != '99999' and arrival3 == '99999':
            bus_msg = "{} is arriving in {} mins and {} mins.  \n".format(bus['service'], arrival1, arrival2)
        elif arrival1 != '99999' and arrival2 != '99999' and arrival3 != '99999':
            bus_msg = "{} is arriving in {} mins, {} mins and {} mins.  \n".format(bus['service'], arrival1, arrival2, arrival3) 
        full_msg = full_msg + bus_msg
    return full_msg

# Get the current date and time as an offset-aware datetime object
def get_time_differences(current_time,arrival_time):
    if arrival_time != '':
        date_time = datetime.strptime(arrival_time, "%Y-%m-%dT%H:%M:%S%z")
        time_difference = date_time - current_time
        if time_difference.days < 0:
            minutes = -1
            seconds = -1
        else:
            seconds_difference = time_difference.seconds
            minutes, seconds = divmod(seconds_difference, 60)
        return [minutes, seconds]
    else:
        return [99999,99999]

def get_nearest_bus_stops(bus_stop_df, stop_latitude, stop_longitude, radius=200):
    bus_stop_df['distance'] = bus_stop_df.apply(lambda row : calculate_distance_in_df(row, stop_latitude, stop_longitude),axis=1)
    bus_stop_df_filtered = bus_stop_df[bus_stop_df['distance']<= radius]
    bus_stop_df_filtered.sort_values('distance',inplace=True)
    return bus_stop_df_filtered

def calculate_distance_in_df(row, stop_latitude, stop_longitude):
    distance = geopy.distance.distance((row['latitude'], row['longitude']), (stop_latitude, stop_longitude)).meters
    return distance

def get_bus_stop_details(bus_stop_df, bus_stop_no):
    bus_stop_info = bus_stop_df[bus_stop_df['BUS_STOP_N']==int(bus_stop_no)]
    if bus_stop_info.shape[0] > 0:
        loca_desc = bus_stop_info.iloc[0]['LOC_DESC']
        lat = bus_stop_info.iloc[0]['latitude']
        long = bus_stop_info.iloc[0]['longitude']
        return [loca_desc, lat, long]
    else:
        return "No such Bus Stop!"

def get_surrounding_specific_bus_stop(bus_stop_df, lta_api_key, point_lat, point_long, radius=200):
    full_msg = 'Details of all surrounding Bus Stops. \n\n'
    nearest_bus_stop_df = get_nearest_bus_stops(bus_stop_df, point_lat, point_long, radius)
    bus_stop_list = list(nearest_bus_stop_df['BUS_STOP_N'])
    for bus_stop in bus_stop_list:
        bus_stop_result = get_all_bus_arrival_from_bus_stop(bus_stop, lta_api_key)
        bus_stop_message = convert_to_message(bus_stop_df, bus_stop, bus_stop_result)
        full_msg += bus_stop_message + "\n\n"
    return full_msg

def get_specific_bus_stop_specific_bus(bus_stop_df, lta_api_key, bus_stop_no, bus_svc):
    bus_stop_result = get_specific_bus_arrival_from_bus_stop(bus_stop_no, lta_api_key, bus_svc)
    bus_stop_message = convert_to_message(bus_stop_df, bus_stop_no, bus_stop_result)
    return bus_stop_message

def get_specific_bus_stop(bus_stop_df, lta_api_key, bus_stop_no):
    bus_stop_result = get_all_bus_arrival_from_bus_stop(bus_stop_no, lta_api_key)
    bus_stop_message = convert_to_message(bus_stop_df, bus_stop_no, bus_stop_result)
    return bus_stop_message

def get_nearest_bus_stop_details(bus_stop_df, lta_api_key, location, radius=200):
    point_lat = location[0]
    point_long = location[1]
    full_msg = 'Details of all Bus Stops around your location. \n\n'
    nearest_bus_stop_df = get_nearest_bus_stops(bus_stop_df, point_lat, point_long, radius)
    bus_stop_list = list(nearest_bus_stop_df['BUS_STOP_N'])
    for bus_stop in bus_stop_list:
        bus_stop_result = get_all_bus_arrival_from_bus_stop(bus_stop, lta_api_key)
        bus_stop_message = convert_to_message(bus_stop_df, bus_stop, bus_stop_result)
        full_msg += bus_stop_message + "\n\n"
    return full_msg

def get_home(bus_stop_df, lta_api_key, location, radius=200):
    home_lat = location[0]
    home_long = location[1]
    full_msg = 'Details of all Bus Stops around Home. \n\n'
    nearest_bus_stop_df = get_nearest_bus_stops(bus_stop_df, home_lat, home_long, radius)
    bus_stop_list = list(nearest_bus_stop_df['BUS_STOP_N'])
    for bus_stop in bus_stop_list:
        bus_stop_result = get_all_bus_arrival_from_bus_stop(bus_stop, lta_api_key)
        bus_stop_message = convert_to_message(bus_stop_df, bus_stop, bus_stop_result)
        full_msg += bus_stop_message + "\n\n"
    return full_msg

def get_go_to_work(bus_stop_df, lta_api_key, radius=200):
    full_msg = 'Bus to take to go work. \n\n'
    bus_stop_list = [46581,46011,46019]
    for bus_stop in bus_stop_list:
        bus_stop_result = get_all_bus_arrival_from_bus_stop(bus_stop, lta_api_key)
        bus_stop_message = convert_to_message(bus_stop_df, bus_stop, bus_stop_result)
        full_msg += bus_stop_message + "\n\n"
    return full_msg

def get_generic_nearest_bus_stop_details(bus_stop_df, lta_api_key, msg_header, location, radius=200):
    lat = location[0]
    long = location[1]
    full_msg = msg_header + '  \n\n'
    nearest_bus_stop_df = get_nearest_bus_stops(bus_stop_df, lat, long, radius)
    bus_stop_list = list(nearest_bus_stop_df['BUS_STOP_N'])
    for bus_stop in bus_stop_list:
        bus_stop_result = get_all_bus_arrival_from_bus_stop(bus_stop, lta_api_key)
        bus_stop_message = convert_to_message(bus_stop_df, bus_stop, bus_stop_result)
        full_msg += bus_stop_message + "\n\n"
    return full_msg
