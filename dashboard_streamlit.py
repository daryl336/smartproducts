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

def load_deshu_counts_file(uploaded_file):
    file_name = uploaded_file.name
    # 
    with st.spinner("Loading {} ...".format(file_name)):
        temp_dir = tempfile.TemporaryDirectory()
        temp_filepath = os.path.join(temp_dir.name,file_name)

        # Save the uploaded file to the temporary directory
        with open(temp_filepath, 'wb') as f:
            f.write(uploaded_file.getvalue())

        if file_name.endswith('.csv'):
            with open(temp_filepath, 'r', encoding='utf-8-sig') as file:
                reader = csv.reader(file)
                data = list(reader)

                # Transpose the data to read values from columns
                transposed_data = list(zip(*data))
                groups = list(transposed_data[0][1:])
                sizes = list(transposed_data[1][1:])
                # Keep the copy in session_state
                st.session_state.deshu_counts_file = reader
                st.session_state.deshu_name = groups
                st.session_state.deshu_size = sizes 
                st.session_state.deshu_dictionary = dict(zip(groups,sizes))
        else:
            st.error('Please upload the correct csv file!', icon="🚨")

def load_grouping_capacity_file(uploaded_file):
    file_name = uploaded_file.name
    # 
    with st.spinner("Loading {} ...".format(file_name)):
        temp_dir = tempfile.TemporaryDirectory()
        temp_filepath = os.path.join(temp_dir.name,file_name)

         # Save the uploaded file to the temporary directory
        with open(temp_filepath, 'wb') as f:
            f.write(uploaded_file.getvalue())

        if '.csv' in file_name:
            with open(temp_filepath, 'r', encoding='utf-8-sig') as file:
                reader = csv.reader(file)
                data = list(reader)
                # Transpose the data to read values from columns
                transposed_data = list(zip(*data))
                bus_names = list(transposed_data[0][1:])
                bus_capacities = list(transposed_data[1][1:])

                # Keep the copy in session_state
                st.session_state.grouping_capacity_file = reader
                st.session_state.grouping_name = bus_names
                st.session_state.grouping_capacity = bus_capacities 
        else:
            st.error('Please upload the correct csv file!', icon="🚨")

# Function to generate and download CSV file
def download_csv(dataframe, filename):
    csv = dataframe.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv">Download {filename} CSV File</a>'
    st.markdown(href, unsafe_allow_html=True)

def main():
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
    # Sample data
    deshu_list = ['1. 忠恕德 (忠德)','1A. 忠恕德 (恕德)','2. 明德','3. 宽德','4. 孝德','5. 仁德','6. 慈德','7. 信忍德 (信德)','7A. 信忍德 (忍德)','8. 公德','9. 博德 (义)','9A. 博德 (三)','10. 廉德','11. 爱德','12. 智德','13. 觉德','14. 节德','15. 俭德','16. 悌德','17. 正义德 (正德)','17A. 正义德 (义德)','18. 真德','19. 礼德','20. 敬德','21. 耻德','22. 温德','23. 良德','24. 和德','25. 峇淡','26. 廖内']
    #sample_group_data = pd.DataFrame(dict(zip([f"Group {i}" for i in range(1,10)],[[30] for i in range(1,10)])))
    #sample_deshu_data = pd.DataFrame(dict(zip(deshu_list,[[30] for i in range(len(deshu_list))])))

    sample_group_data = pd.DataFrame({'group_names' : [f"Group {i}" for i in range(1,11)],'max_capacities' : [30 for i in range(1,11)]})
    sample_deshu_data = pd.DataFrame({'deshu_names' : deshu_list,'counts' : [30 for i in range(len(deshu_list))]})
    st.set_page_config(page_title="Suggested Grouping Classification", layout="wide")    
    st.title("Suggested Grouping Classification")
    st.subheader('Instructions!', divider='rainbow')    
    st.write("Step 1 : Download the template files and fill up the details.")
    st.write("Step 2 : Upload the correct CSV files at the correct section.")
    st.write("Step 3 : [Optional] Select the Deshus that needs to be together in the same group.")
    st.write("Step 4: If the above steps are done correctly, the suggested results will be generated below.")

    st.write("")
    st.write("")

    st.subheader('Download Template Files here! Do not amend the table headers!', divider='rainbow')
    st.write("Deshu Counts CSV file - Contains the number of pax within each Deshu. (e.g. Camp Participants, TWJX Participants, 乾道 for Room arrangement)")
    if st.button('Download Deshu Counts CSV file'):
        download_csv(sample_deshu_data, 'deshu_counts')
    st.write("Group Capacity CSV file - Contains the maximum number of pax within each group. Group can refers to Camp Group, or a room, or a bus.")
    st.write("You are free to use any names for the groups, and no maximum number of the group. (i.e. Group 1, Group 2, ... , Group 10   OR   Room 401 , ... , Room 502   OR   Bus 1 , ... , Bus 10)")
    if st.button('Download Group Capacity CSV file'):
        download_csv(sample_group_data, 'capacities')
    
    st.write("")
    st.write("")

    st.subheader('Upload Files here!', divider='rainbow')
    deshu_counts = st.file_uploader(label='Upload Deshu Counts CSV file here!')
    if deshu_counts:
        load_deshu_counts_file(deshu_counts)
    grouping_counts = st.file_uploader(label='Upload Grouping Capacity CSV file here!')
    if grouping_counts:
        load_grouping_capacity_file(grouping_counts)

    st.write("")
    st.write("")

    st.subheader('Select Deshu to be together in the same group [Optional]', divider='rainbow')
    # Create two dropdowns for selecting groups
    selected_group_1 = st.selectbox('Select 1st Deshu:', deshu_list)
    selected_group_2 = st.selectbox('Select 2nd Deshu:', deshu_list)

    # Button to insert selected items into the list
    if st.button('Add both deshus together'):
        st.session_state.deshu_group_edge.append((selected_group_1,selected_group_2))

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

    if groups and sizes and bus_names and bus_capacities:
        allocations, assigned_groups, remaining_capacities, bus_names, groups = streamlit_main(groups, sizes, bus_names, bus_capacities, bus_edges)
        streamlit_write_results(allocations, assigned_groups, remaining_capacities, bus_names, groups)
    else:
        st.write("Please insert the corresponding files!")

def streamlit_write_results(allocations, assigned_groups, remaining_capacities, bus_names, groups):
    # Print the results
    deshu = []
    deshu_count = []
    group = []
    for bus, allocated_groups in allocations.items():
        if allocated_groups:
            name = bus_names[bus-1]
            count = 0
            res = f"{name} -"
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
    if st.button('Download Suggested Classification Results'):
        download_csv(final_result, 'Suggested Classification Results')
    

if __name__ == "__main__":
    main()
