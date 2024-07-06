from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
import os

#paramters
ID = 'GPM01'
SCOPES = ['https://www.googleapis.com/auth/drive']

def _print(message):
    current_time = datetime.now()
    formatted_time = current_time.strftime("[%d/%m/%Y - %H:%M:%S]")
    print(f"{formatted_time} :: {message}")

def gdrive_parent():
    GDrive_parents = {
    'GPM01': ['1SLzhGyupTPCfIizgmZMY2fgN2h9hjEIg'],
    'GPM02': ['1-8xAEW3ruXRWxyGtj0YuSGR1J3dBP8vs'],
    'GPM03': ['1UoN3C_vs46xHTpt_2aInWO-lCgL7jQfR'],
    'GPM04': ['1BMrQIb6QzQz7M5hq2JGBoMUBddX7fn5H'],
    'GPM05': ['1LYKhP7VfApcbr2gLmoBnNAO9H0YmRtEV'],
    'GPM06': ['1poLnFssMt_FHmnn1UCfsbEbyiuk_b6EZ'],
    'GPM07': ['1ENCerFyDZZOLPZxkLumB2XrWl0kOXKcM'],
    'GPM08': ['1Kd38xGspSFZgzLzQnKFVCP4UZsyEbvQx']}
    return GDrive_parents[ID]

def log_in_google():
    creds = None
    if os.path.exists("/home/pi/token.json"):
        creds = Credentials.from_authorized_user_file("/home/pi/token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("/home/pi/credentials.json", SCOPES)
            creds = flow.run_local_server(port=0) 
    with open("/home/pi/token.json", "w") as token:
      token.write(creds.to_json())
    return creds

def upload_logs(creds, parent):
    ia4g_log = "/home/pi/IA4G.log"
    file_id = upload_logs_core(creds, ia4g_log, parent)
    #wittyPi_log = "/home/pi/wittypi/wittyPi.log"
    #file_id = upload_logs_core(creds, wittyPi_log, parent)
    #schedule_log = "/home/pi/wittypi/schedule.log"
    #file_id = upload_logs_core(creds, schedule_log, parent)

def upload_logs_core(creds, file_path, parent):
    try:
        service = build("drive", "v3", credentials=creds)
        media = MediaFileUpload(file_path, mimetype='text/plain')
        file_name = os.path.basename(file_path)
        query = f"name='{file_name}' and '{parent[0]}' in parents and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        items = results.get('files', [])
        file_metadata = {'name': os.path.basename(file_path), "addParents": parent[0]}

        if items:
            file_id = items[0]['id']
            try:
                updated_file = service.files().update(fileId=file_id, body=file_metadata, media_body=media).execute()
                _print(f'File ID: {updated_file.get("id")} overwritted')
            except:
                updated_file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
                _print(f'File ID: {updated_file.get("id")} uploaded')
        else:
            updated_file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
            _print(f'File ID: {updated_file.get("id")}')

    except HttpError as error:
        _print(f"ERROR: An error occurred: {error}")

if __name__ == "__main__":
    parent = gdrive_parent()
    creds = log_in_google()
    upload_logs(creds, parent)
