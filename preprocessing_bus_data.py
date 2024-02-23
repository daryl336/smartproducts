import requests
import json
import geopy.distance
import pandas as pd
import geopandas as gpd
from datetime import datetime, timedelta, timezone
import vertexai
from vertexai.preview.language_models import TextEmbeddingModel, TextGenerationModel
from google.oauth2 import service_account
import streamlit as st

type = st.secrets["type"]
project_id = st.secrets["project_id"]
private_key_id = st.secrets["private_key_id"]
private_key = st.secrets["private_key"]
client_email = st.secrets["client_email"]
client_id = st.secrets["client_id"]
auth_uri = st.secrets["auth_uri"]
token_uri  = st.secrets["token_uri"]
auth_provider_x509_cert_url  = st.secrets["auth_provider_x509_cert_url"]
client_x509_cert_url  = st.secrets["client_x509_cert_url"]
universe_domain  = st.secrets["universe_domain"]
location = st.secrets["location"]
LTA_API_KEY = st.secrets["LTA_API_KEY"]

credentials_details = {
  "type": type,
  "project_id": project_id,
  "private_key_id": private_key_id,
  "private_key": private_key,
  "client_email": client_email,
  "client_id": client_id,
  "auth_uri": auth_uri,
  "token_uri": token_uri,
  "auth_provider_x509_cert_url": auth_provider_x509_cert_url,
  "client_x509_cert_url": client_x509_cert_url,
  "universe_domain": universe_domain
}
#credentials = service_account.Credentials.from_service_account_file('genaisa.json')
credentials = service_account.Credentials.from_service_account_info(credentials_details)
project_id = st.secrets["project_id"]
location = st.secrets["location"]

url = "http://datamall2.mytransport.sg/ltaodataservice/BusRoutes"
headers = {'AccountKey': LTA_API_KEY}

result = []
for i in range(100):
    if i == 0:
        url = "http://datamall2.mytransport.sg/ltaodataservice/BusRoutes"
        response = requests.get(url, headers=headers)
        data = response.json()
        result.append(data['value'])
    else:
        skip = str(i* 500)
        url = "http://datamall2.mytransport.sg/ltaodataservice/BusRoutes?$skip={}".format(skip)
        response = requests.get(url, headers=headers)
        data = response.json()
        result.append(data['value'])


unique_bus_services = []
bus_info = {}

for d in result:
    for bus in d:
        if bus['ServiceNo'] not in unique_bus_services:
            unique_bus_services.append(bus['ServiceNo'])
            bus_info[bus['ServiceNo']] = {'Direction':[]}

for res in result:
    for b in res:
        svc = b['ServiceNo']
        if b['Direction'] not in bus_info[svc]['Direction']:
            bus_info[svc]['Direction'].append(b['Direction'])
            bus_info[svc]['Timing '+str(b['Direction'])] = {'WD_FirstBus':b['WD_FirstBus'], 'WD_LastBus': b['WD_LastBus'], 'SAT_FirstBus': b['SAT_FirstBus'], 'SAT_LastBus': b['SAT_LastBus'], 'SUN_FirstBus': b['SUN_FirstBus'], 'SUN_LastBus': b['SUN_LastBus']}

bus_stop_details = []
for i in range(100):
    if i == 0:
        url = "http://datamall2.mytransport.sg/ltaodataservice/BusStops"
        response = requests.get(url, headers=headers)
        data = response.json()
        bus_stop_details.append(data['value'])
    else:
        skip = str(i* 500)
        url = "http://datamall2.mytransport.sg/ltaodataservice/BusStops?$skip={}".format(skip)
        response = requests.get(url, headers=headers)
        data = response.json()
        bus_stop_details.append(data['value'])

unpack = {'BUS_STOP_N':[],'LOC_DESC':[],'latitude':[],'longitude':[]}
for i in bus_stop_details:
    for bs in i:
        unpack['BUS_STOP_N'].append(bs['BusStopCode'])
        unpack['LOC_DESC'].append(bs['Description'])
        unpack['latitude'].append(bs['Latitude'])
        unpack['longitude'].append(bs['Longitude'])


bus_stop_details_dict = {}
for i in bus_stop_details:
    for bs in i:
        bus_stop_details_dict[bs['BusStopCode']] = {'RoadName':bs['RoadName'],'Description':bs['Description'],'Latitude':bs['Latitude'],'Longitude':bs['Longitude']}

for bus in list(bus_info.keys()):
    for dir in bus_info[bus]['Direction']:
        route_list = []
        full_route_list = []
        for d in result:
            for b in d:
                if b['ServiceNo']== bus and b['Direction'] == dir:
                    route_list.append(b['BusStopCode'])
                    full_route_list.append(b['BusStopCode'] + ': ' + bus_stop_details_dict[b['BusStopCode']]['Description'])
        bus_info[bus]['route '+str(dir)] = route_list
        bus_info[bus]['full route '+str(dir)] = full_route_list

bus_info['50']

bus_info_full = {'bus_service':[],'bus_service_info':[]}

for bus in list(bus_info.keys()):
    bus_info_full['bus_service'].append(bus)
    first_last_bus_info = ''
    direction_info = ''
    full_route_info = ''
    direction = bus_info[bus]['Direction']
    if len(direction) == 2:
        direction_info = 'Direction of Travel: Bus Service {} has {} directions. The first direction is towards {} while the second direction is towards {}.'.format(bus, str(len(direction)), bus_info[bus]['full route 1'][-1], bus_info[bus]['full route 2'][-1])
        first_last_bus_info = 'Bus Timing Information: The timings are as follows:'
        dir1_info = 'Towards {}  \n'.format(bus_info[bus]['full route 1'][-1]) + 'Weekday First Bus : {}, Weekday Last Bus : {}'.format(bus_info[bus]['Timing 1']['WD_FirstBus'],bus_info[bus]['Timing 1']['WD_LastBus']) + ', Saturday First Bus : {}, Saturday Last Bus : {}'.format(bus_info[bus]['Timing 1']['SAT_FirstBus'],bus_info[bus]['Timing 1']['SAT_LastBus']) + ', Sunday First Bus : {}, Sunday Last Bus : {}'.format(bus_info[bus]['Timing 1']['SUN_FirstBus'],bus_info[bus]['Timing 1']['SUN_LastBus'])
        dir2_info = 'Towards {}  \n'.format(bus_info[bus]['full route 2'][-1]) + 'Weekday First Bus : {}, Weekday Last Bus : {}'.format(bus_info[bus]['Timing 2']['WD_FirstBus'],bus_info[bus]['Timing 2']['WD_LastBus']) + ', Saturday First Bus : {}, Saturday Last Bus : {}'.format(bus_info[bus]['Timing 2']['SAT_FirstBus'],bus_info[bus]['Timing 2']['SAT_LastBus']) + ', Sunday First Bus : {}, Sunday Last Bus : {}'.format(bus_info[bus]['Timing 2']['SUN_FirstBus'],bus_info[bus]['Timing 2']['SUN_LastBus'])
        first_last_bus_info = first_last_bus_info + '  \n' + dir1_info + '  \n' + dir2_info
        full_route_1 = 'Towards {}  \nRoute List:'.format(bus_info[bus]['full route 1'][-1])
        for bs in bus_info[bus]['full route 1']:
            full_route_1 = full_route_1 + '  \n' + bs
        full_route_2 = 'Towards {}  \nRoute List:'.format(bus_info[bus]['full route 2'][-1])
        for bs in bus_info[bus]['full route 2']:
            full_route_2 = full_route_2 + '  \n' + bs
        full_route_info = full_route_1 + '\n\n' + full_route_2
    else:
        direction_info = 'Direction of Travel: Bus Service {} is a loop service which starts at {}.'.format(bus, bus_info[bus]['full route 1'][-1])
        first_last_bus_info = 'Bus Timing Information: The timings are as follows:  \n Loop Service starting at {}  \n'.format(bus_info[bus]['full route 1'][-1]) + 'Weekday First Bus : {}, Weekday Last Bus {}'.format(bus_info[bus]['Timing 1']['WD_FirstBus'],bus_info[bus]['Timing 1']['WD_LastBus']) + ', Saturday First Bus : {}, Saturday Last Bus : {}'.format(bus_info[bus]['Timing 1']['SAT_FirstBus'],bus_info[bus]['Timing 1']['SAT_LastBus']) + ', Sunday First Bus : {}, Sunday Last Bus : {}'.format(bus_info[bus]['Timing 1']['SUN_FirstBus'],bus_info[bus]['Timing 1']['SUN_LastBus'])
        full_route_1 = 'Towards {}  \nRoute List:'.format(bus_info[bus]['full route 1'][-1])
        for bs in bus_info[bus]['full route 1']:
            full_route_1 = full_route_1 + '  \n' + bs
        full_route_info = full_route_1
    total = 'Bus Service {} Information'.format(bus) + '\n\n' + direction_info + '\n\n' + first_last_bus_info + '\n\n' + full_route_info
    bus_info_full['bus_service_info'].append(total)

bus_info_df = pd.DataFrame(bus_info_full)
bus_info_df.to_excel('Bus Services Info.xlsx',index=False)

# Initiate Vertex AI
vertexai.init(project=project_id, location=location, credentials = credentials)

model = TextEmbeddingModel.from_pretrained("google/textembedding-gecko@001")

# This function takes a text string as input
# and returns the embedding of the text
def get_embedding(text: str) -> list:
    try:
        embeddings = model.get_embeddings([text])
        return embeddings[0].values
    except:
        return []

bus_info_df["bus_service_embedding"] = bus_info_df["bus_service"].apply(lambda x: get_embedding(x))

embed_dict = {}
for index, row in bus_info_df.iterrows():
    embed_dict[row.bus_service] = [row.bus_service_embedding,row.bus_service_info]

with open('bus_service_embeddings.json', 'w') as json_file:
    json.dump(embed_dict, json_file)

