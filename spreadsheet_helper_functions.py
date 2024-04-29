import os
import google.auth
from google.oauth2 import service_account
from googleapiclient.discovery import build
from filepath import creds_filename


def authoriseServiceAccountForSheets(creds_filename):
    # Load the service account credentials from a JSON file
    if type(creds_filename) == str:
        creds = service_account.Credentials.from_service_account_file(creds_filename)
    elif type(creds_filename) == dict:
        creds = service_account.Credentials.from_service_account_info(creds_filename)
    # Authenticate and authorize the service account
    service = build('sheets', 'v4', credentials=creds)
    return service

def appendRegistrationData(service,spreadsheet_id,sheet_name,range_cells,values):
    ''' Through a conversation, collate data and append into spreadsheet'''
    # Call the Sheets API to read data from a sheet
    range_name = sheet_name+'!'+range_cells
    result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            body={'values': values}).execute()

def getRangeData(service,spreadsheet_id,sheet_name,range_cells):
    range_name = sheet_name+'!'+range_cells
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    single_list_of_values = sum(values, [])
    return single_list_of_values

def updateRangeData(service,spreadsheet_id,sheet_name,range_cells,df):
    range_name = sheet_name+'!'+range_cells
    data = df.values.tolist()
    body = {
        'values': data
    }
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='RAW',
        body=body
    ).execute()
    return True

def checkRegistration(service,spreadsheet_id,sheet_name,range_cells,user_id):
    ''' Check if the user is an existing user or new user.'''
    range_name = sheet_name+'!'+range_cells
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    single_list_of_values = sum(values, [])
    # Check if any cell in the range contains the value 'example'
    return user_id in single_list_of_values

def getWholeRowDataUsingUserID(service,spreadsheet_id,sheet_name,range_cells,user_id):
    ''' Get the row of the user id '''
    range_name = sheet_name+'!'+range_cells
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    filtered_list = list(filter(lambda sublist: user_id in sublist, values))
    return filtered_list

def getRowFromUserID(service,spreadsheet_id,sheet_name,range_cells,user_id):
    ''' Get the row of the user id '''
    range_name = sheet_name+'!'+range_cells
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    row = values.index([user_id])+1
    return row

def getChineseName(service,spreadsheet_id,sheet_name,user_id):
    ''' Get the Chinese Name of the specified user '''
    row = getRowFromUserID(service,spreadsheet_id,sheet_name,'C:C',user_id)
    range_name = sheet_name+'!A'+str(row)
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    chinese_name = result.get('values', [[]])[0][0]
    return chinese_name

def getRowUsingDeshu(service,spreadsheet_id,sheet_name,range_cells,deshu):
    ''' Get the row of the deshu '''
    range_name = sheet_name+'!'+range_cells
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    row = values.index([deshu])+1
    return row

def getDeshuSpreadsheetID(service,spreadsheet_id,sheet_name,deshu_column,ssid_column,deshu):
    ''' Get the row of the deshu and return the spreadsheet id '''
    deshu_range_name = sheet_name+'!'+deshu_column+':'+deshu_column
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=deshu_range_name).execute()
    values = result.get('values', [])
    row = values.index([deshu])+1
    ssid_range_name = sheet_name+'!'+ssid_column+str(row)
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=ssid_range_name).execute()
    ssid = result.get('values', [[]])[0][0]
    return ssid

def getLastRow(service,spreadsheet_id,sheet_name,range_column):
    ''' Get the last row of the sheet '''
    range_name = sheet_name+'!'+range_column+':'+range_column
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    last_row = len(values)
    return last_row

def getCampLastRow(service,spreadsheet_id,sheet_name,range_column):
    ''' Get the last row of the sheet '''
    range_name = sheet_name+'!'+range_column+':'+range_column
    result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
    values = result.get('values', [])
    last_row = len(values)-11
    return last_row

'''
spreadsheet_id = '1FPsDGCMgJOvthOPDJPihdFVYBBlF0NvSTw8a3JEs-OI'
sheet_name = 'Registration'
range_cells = 'C:C'
existing_user = checkRegistration(service,spreadsheet_id,sheet_name,range_cells,str(220268210))
chinese_name = getChineseName(service,spreadsheet_id,sheet_name,str(220268210))

print(chinese_name)
'''

'''
For Camp Spreadsheet

spreadsheet_id = '1XseWnnPW8L-67t-EF9m6kwtMWtrblLo2D4C82b3RkRw'
sheet_name = 'Details'
deshu_column = 'A'
ssid_column = 'B'
deshu = '14A. 爱(盛港)'
ssid = getDeshuSpreadsheetID(service,spreadsheet_id,sheet_name,deshu_column,ssid_column,deshu)
'''

'''
service = authoriseServiceAccountForSheets(creds_filename)
spreadsheet_id = '1XseWnnPW8L-67t-EF9m6kwtMWtrblLo2D4C82b3RkRw'
sheet_name = 'Details'
deshu_column = 'A'
ssid_column = 'B'
deshu_camp_ssid = getDeshuSpreadsheetID(service,spreadsheet_id,sheet_name,deshu_column,ssid_column,"14A. 爱(盛港)")
    
sheet_last_row = getCampLastRow(service,deshu_camp_ssid,"CD Camp","A")
user_processed_data = ["ABCD","参学者","93376520"]
appendRegistrationData(service,deshu_camp_ssid,"CD Camp","A:A",[[sheet_last_row+1]+user_processed_data])
'''

'''
user_id = '220268210'
service = authoriseServiceAccountForSheets(creds_filename)
spreadsheet_id = '1FPsDGCMgJOvthOPDJPihdFVYBBlF0NvSTw8a3JEs-OI'
sheet_name = 'Past Registration Data'
range_cells = 'A:K'
data = getWholeRowDataUsingUserID(service,spreadsheet_id,sheet_name,range_cells,user_id)

if data == []:
    print("NO values!")
else:
    print("Yes there are values.")

keys = ['chinese_name','deshu','gender','level','mobile','food_allergy','med_allergy','ename','emobile','erelationship']
values = data[0]

dictionary = {k: v for k, v in zip(keys, values)}


service = authoriseServiceAccountForSheets(creds_filename)
spreadsheet_id = '18glM0s2Z0FGwShbsRedVnVddJH1Ax0psUbS_DopDpqs'
sheet_name = 'Groups'
range_cells = 'A2:A999'
deshu_names = getRangeData(service,spreadsheet_id,sheet_name,range_cells)
'''