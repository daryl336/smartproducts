import os
#__import__('pysqlite3')
import sys
#sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import tempfile
import streamlit as st 
from bus_algo import streamlit_main
import csv
import networkx as nx
import pandas as pd
import base64
import spreadsheet_helper_functions as shelper
from google.oauth2 import service_account

def load_credentials():
    type = st.secrets["type"]
    project_id = st.secrets["project_id2"]
    private_key_id = st.secrets["private_key_id2"]
    private_key = st.secrets["private_key2"]
    client_email = st.secrets["client_email2"]
    client_id = st.secrets["client_id2"]
    auth_uri = st.secrets["auth_uri2"]
    token_uri  = st.secrets["token_uri2"]
    auth_provider_x509_cert_url  = st.secrets["auth_provider_x509_cert_url2"]
    client_x509_cert_url  = st.secrets["client_x509_cert_url2"]

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
    }
    return credentials_details

def load_data_from_twjx(event):
    credentials_details = load_credentials()
    service = shelper.authoriseServiceAccountForSheets(credentials_details)
    spreadsheet_id = ''
    twjx_main_id = "1IYSmKJVgD4DZ3BFfd0Ij3R4w4LzK3S_JY4M9NubL3VA"

    if event == "Bus":
        spreadsheet_id = twjx_main_id
        sheet_name = 'Generate Bus Arrangements'
        st.session_state.event_selected = "Bus"
    elif event == "Room":
        spreadsheet_id = twjx_main_id
        sheet_name = 'Generate Room Arrangements'
        st.session_state.event_selected = "Room"

    if spreadsheet_id != '':
        ### Load Deshu Names 
        range_cells = 'H3:H40'
        deshu_names = shelper.getRangeData(service,spreadsheet_id,sheet_name,range_cells)
        st.session_state.deshu_name = deshu_names

        ### Load Deshu Counts
        range_cells = 'I3:I40'
        deshu_counts = shelper.getRangeData(service,spreadsheet_id,sheet_name,range_cells)
        st.session_state.deshu_size = deshu_counts 
        st.session_state.deshu_dictionary = dict(zip(deshu_names,deshu_counts))

        ### Load Group Names and Max Capacity.
        range_cells = 'E3:E999'
        group_names = shelper.getRangeData(service,spreadsheet_id,sheet_name,range_cells)
        st.session_state.grouping_name = group_names
                
        range_cells = 'F3:F999'
        deshu_counts = shelper.getRangeData(service,spreadsheet_id,sheet_name,range_cells)
        st.session_state.grouping_capacity = deshu_counts

        st.session_state.data_loaded = True
        st.success('Data for {} successfully loaded!'.format(event), icon="✅")


def twjx_update_suggested_grouping(event,df):
    credentials_details = load_credentials()
    service = shelper.authoriseServiceAccountForSheets(credentials_details)
    spreadsheet_id = ''
    twjx_main_id = "1IYSmKJVgD4DZ3BFfd0Ij3R4w4LzK3S_JY4M9NubL3VA"

    if event == "Bus":
        spreadsheet_id = twjx_main_id
        sheet_name = 'Generate Bus Arrangements'
    elif event == "Room":
        spreadsheet_id = twjx_main_id
        sheet_name = 'Generate Room Arrangements'

    if spreadsheet_id != '':
        range_cells = 'A3'
        if shelper.updateRangeData(service,spreadsheet_id,sheet_name,range_cells,df):
            st.success('Suggested Grouping Updated for {}! '.format(event), icon="✅")
        else:
            st.error("Please check the data in the respective range!")

def twjx_suggest_grouping():
    # deshu_count.csv
    if 'deshu_counts_file' not in st.session_state:
        st.session_state.deshu_counts_file = None
    # groups
    if 'deshu_name' not in st.session_state:
        st.session_state.deshu_name = None
    # sizes
    if 'deshu_size' not in st.session_state:
        st.session_state.deshu_size = None
    # capacities.csv
    if 'deshu_dictionary' not in st.session_state:
        st.session_state.deshu_dictionary = None
    # capacities.csv
    if 'grouping_capacity_file' not in st.session_state:
        st.session_state.grouping_capacity_file = None
    # bus_names
    if 'grouping_name' not in st.session_state:
        st.session_state.grouping_name = None
    # bus_capacities
    if 'grouping_capacity' not in st.session_state:
        st.session_state.grouping_capacity = None
    # deshu_group
    if 'deshu_group_edge' not in st.session_state:
        st.session_state.deshu_group_edge = []
    # Camp or Bus or Room
    if 'event_selected' not in st.session_state:
        st.session_state.event_selected = None
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = None

    if event_selected != '< Select >':
        if event_selected != st.session_state.event_selected:
            with st.spinner("Loading {} data ...".format(event_selected)):
                load_data_from_twjx(event_selected)
        else:
            if st.session_state.data_loaded:
                st.success('Data from {} successfully loaded!'.format(event_selected), icon="✅")
                
    deshu_list = st.session_state.deshu_name
    if deshu_list:
        print(deshu_list)
    else:
        deshu_list = []
    st.title("Suggested Grouping Classification")

    st.subheader('Instructions!', divider='rainbow')    
    st.write("Deshu and Grouping (Bus / Room data) is obtained from TWJX Admin Spreadsheet in the Generate Bus Arrangements / Generate Room Arrangements sheet.")
    st.write("TWJX Admin Spreadsheet: https://docs.google.com/spreadsheets/d/1IYSmKJVgD4DZ3BFfd0Ij3R4w4LzK3S_JY4M9NubL3VA/edit?gid=1645101658#gid=1645101658")
    st.write("Suggested groupings will be output and found in the same sheet")
    st.write("You can further split the deshu into smaller groups and set the capacity as and when appropriate.")

    st.write("")
    st.write("")

    st.subheader('Select Bus or Room!', divider='rainbow')
    # Create two dropdowns for selecting groups
    event_selected = st.selectbox('Select Bus or Room', ['< Select >','Bus', 'Room'],index=0)
    st.write("")
    st.write("")

    
            
    st.subheader('Select Deshu to be together in the same group [Optional]', divider='rainbow')
    # Create two dropdowns for selecting groups
    selected_group_1 = st.selectbox('Select 1st Deshu:', ['< Select >'] + deshu_list)
    selected_group_2 = st.selectbox('Select 2nd Deshu:', ['< Select >'] + deshu_list)
    
    # Button to insert selected items into the list
    if st.button('Add both deshus together'):
        if selected_group_1 in deshu_list and selected_group_2 in deshu_list:
            if (selected_group_1,selected_group_2) not in st.session_state.deshu_group_edge:
                st.session_state.deshu_group_edge.append((selected_group_1,selected_group_2))
        else:
            st.error('Please select the deshus!', icon="🚨")

    st.write("")
    st.write("")

    # Display the selected groups in the edge
    st.subheader('Current Selected Deshu Pairing (To Be In Same Group)', divider='rainbow')
    i = 0
    if st.session_state.deshu_group_edge == []:
        st.write("No Deshus to be put together!")
    else:
        for pair in st.session_state.deshu_group_edge:
            i = i + 1
            st.write(f'Pair {i} : ', pair[0] + ' & ' + pair[1])
    
    st.write("")
    st.write("")

    st.subheader('Classification Results', divider='rainbow')

    groups = st.session_state.deshu_name
    sizes = st.session_state.deshu_size
    bus_names = st.session_state.grouping_name
    bus_capacities = st.session_state.grouping_capacity
    bus_edges = st.session_state.deshu_group_edge

    if st.button('Regenerate results'):
        load_data_from_twjx(event_selected)
        if groups and sizes and bus_names and bus_capacities:
            allocations, assigned_groups, remaining_capacities, bus_names, groups = streamlit_main(groups, sizes, bus_names, bus_capacities, bus_edges)
            streamlit_write_results(allocations, assigned_groups, remaining_capacities, bus_names, groups, event_selected)
    else:
        if groups and sizes and bus_names and bus_capacities:
            allocations, assigned_groups, remaining_capacities, bus_names, groups = streamlit_main(groups, sizes, bus_names, bus_capacities, bus_edges)
            streamlit_write_results(allocations, assigned_groups, remaining_capacities, bus_names, groups, event_selected)

def streamlit_write_results(allocations, assigned_groups, remaining_capacities, bus_names, groups, camp_selected):
    # Print the results
    deshu = []
    deshu_count = []
    group = []
    for bus, allocated_groups in allocations.items():
        if allocated_groups:
            name = bus_names[bus-1]
            count = 0
            res = f"{name} - "
            for i in allocated_groups:
                res = res + i[0] + '   '
                count = count + i[1]

                deshu.append(i[0])
                deshu_count.append(i[1])
                group.append(name)

            st.write(res)
            st.write("Total : "+str(count) + ", Remaining Capacity : " + str(remaining_capacities[bus-1]))
            st.write("")
        else:
            name = bus_names[bus-1]
            st.write(f"{name} - No Deshu allocated")
            st.write("")
    # Calculate unassigned groups
    unassigned_groups = set(groups) - assigned_groups
    st.write(f"Unassigned Deshu: {list(unassigned_groups)}")
    for j in unassigned_groups:
        deshu.append(j)
        deshu_count.append(st.session_state.deshu_dictionary[j])
        group.append('Unassigned')
    final_result = pd.DataFrame({'Deshu' : deshu,'Deshu Count' : deshu_count, 'Assigned Group' : group})
    twjx_update_suggested_grouping(camp_selected,final_result)


if __name__ == "__main__":
    twjx_suggest_grouping()
