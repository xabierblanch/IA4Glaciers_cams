##############################################################################################
# GDrive_images: Script to upload TIR images to Google Drive                   #
#                                                                                            #
# Author: Xabier Blanch Gorriz                                                               #
#                                                                                            #
# This script is open-source and licensed under the MIT License.                             #
# Technische Universität Dresden in collaboration with Universitat Politecnica de Catalunya  #
#                                                                                            #
# Copyright (c) XBG 2024                                                                     #
##############################################################################################

import time
start_time = time.time()
from datetime import datetime
import os
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import argparse
import random

parser = argparse.ArgumentParser(description='GDrive script to upload TIR images')
parser.add_argument('--id', type=str, required=True, help='ID for the system')
parser.add_argument('--filetype', type=str, required=True, choices=['LOG', 'RGB', 'TIR'], help='Tipo de archivo a subir (log, RGB_Images, TIR_Images)')
args = parser.parse_args()
BASE_PATH = '/home/pi'

ID = args.id
dtype = args.filetype

SCOPES = ['https://www.googleapis.com/auth/drive']
TOKEN_PATH = "/home/pi/scripts/token.json"
CREDENTIALS_PATH = "/home/pi/scripts/credentials.json"
USB_PATH = os.path.join(BASE_PATH, "usb_stick")

def _print(message):
    current_time = datetime.now()
    formatted_time = current_time.strftime("[%d/%m/%Y - %H:%M:%S]")
    print(f"{formatted_time} :: GDrive_{dtype} :: {message}")

def gdrive_parent():
    GDrive_parents = {
    'GPM01': ['1SLzhGyupTPCfIizgmZMY2fgN2h9hjEIg'],
    'GPM02': ['1-8xAEW3ruXRWxyGtj0YuSGR1J3dBP8vs'],
    'GPM03': ['1UoN3C_vs46xHTpt_2aInWO-lCgL7jQfR'],
    'GPM04': ['1BMrQIb6QzQz7M5hq2JGBoMUBddX7fn5H'],
    'GPM05': ['1LYKhP7VfApcbr2gLmoBnNAO9H0YmRtEV'],
    'GPM06': ['1poLnFssMt_FHmnn1UCfsbEbyiuk_b6EZ'],
    'GPM07': ['1ENCerFyDZZOLPZxkLumB2XrWl0kOXKcM'],
    'GPM08': ['1Kd38xGspSFZgzLzQnKFVCP4UZsyEbvQx'],
    'GPM_Dresden': ['11LaYOWSchllfphGBMLj-KEuZZ608TTEO']}
    return GDrive_parents[ID]

def log_in_google():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0) 
    with open(TOKEN_PATH, "w") as token:
      token.write(creds.to_json())
    if creds is not None:
        _print("Logging in Google Drive API succesfully")
    return creds

def create_folders(path):
    try:
        os.makedirs(path, exist_ok = True)
        _print(f"Folder {os.path.basename(path)} created successfully")
    except Exception as e:
        _print(f"ERROR creating folder {os.path.basename(path)}: {e}")  

def exponential_backoff_retry(function, retries=5, initial_wait=1):
    for attempt in range(retries):
        try:
            return function()
        except HttpError as error:
            if error.resp.status in [500, 503]:
                wait_time = initial_wait * (2 ** attempt) + random.uniform(0, 1)
                _print(f"Retrying after {wait_time:.2f}s due to {error}")
                time.sleep(wait_time)
            else:
                raise 
    raise Exception(f"Failed after {retries} attempts")

def resumable_upload(service, file_path, file_metadata):
    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
    request = service.files().create(body=file_metadata, media_body=media, fields="id, name, mimeType")
    response = None
    while response is None:
        try:
            status, response = exponential_backoff_retry(lambda: request.next_chunk())
            if status:  # Upload is in progress
                _print(f"Upload progress: {int(status.progress() * 100)}%")
        except HttpError as error:
            if error.resp.status in [404, 403]:  # Permanent errors
                raise Exception(f"Upload failed due to permission or file not found: {error}")
            _print(f"Temporary error during upload: {error}. Retrying...")
        except Exception as e:
            _print(f"Unexpected error during upload: {e}")
            return None
    
    # After completion, `response` contains file metadata
    if response:
        _print(f"{response.get('name')} succesfully uploaded with id {response.get('id')}")
    return response

def corrupted_file(file_path):
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        _print(f"Invalid or empty file: {file_path}")
        return True
    return False

def google_upload(creds, parent):
    try:
        files = [f for f in os.listdir(path_filetransfer) if f.endswith(file_type)]
        if not files:
            _print(f"No {file_type} files in the FileTransfer folder. No upload process")
            return
            
        _print(f'{len(files)} {file_type} files in the FileTransfer folder. The upload will start:')
        service = build("drive", "v3", credentials=creds)
 
        for file in files:                       
            file_path = os.path.join(path_filetransfer, file)
            if corrupted_file(file_path):
                continue
                
            file_metadata = {"parents": parent, "name":  file}            
            try:
                file_gdrive = resumable_upload(service, file_path, file_metadata)
                #backup_copy(file_gdrive, file, file_path, path_backup)
                delete_uploaded_file(file_gdrive, file, file_path)
            except Exception as e:
                _print(f"Critical error while uploading {file_path}: {e}")
    except:
        _print("Error")     
                
def backup_copy(file_gdrive, file, file_path, path_backup):
    try:
        if file_gdrive and file_gdrive.get("id"):
            backup_path = os.path.join(path_backup, file)
            os.replace(file_path, backup_path)
            _print(f'{file} saved in the backup folder')
        else:
            _print(f'Comprovation in GDrive failed: {os.path.basename(file_path)} will remain on main folder')
    
    except Exception as e:
        _print(f"ERROR during backup process for file {file}: {e}")

def upload_logs_core(creds, file_path, new_name, parent):
    try:
        service = build("drive", "v3", credentials=creds)
        media = MediaFileUpload(file_path, mimetype='text/plain')

        query = f"name='{new_name}' and '{parent[0]}' in parents and trashed=false"
        results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
        items = results.get('files', [])

        if items:
            file_id = items[0]['id']
            try:
                file_metadata = {'name': new_name, "addParents": parent[0]}
                updated_file = service.files().update(fileId=file_id, body=file_metadata, media_body=media).execute()
                _print(f'File ID: {updated_file.get("id")} overwritted')
            except:
                file_metadata = {"parents": parent, "name":  new_name}
                updated_file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
                _print(f'File ID: {updated_file.get("id")} uploaded')
        else:
            file_metadata = {"parents": parent, "name":  new_name}
            updated_file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
            _print(f'File ID: {updated_file.get("id")} uploaded')

    except HttpError as error:
        _print(f"ERROR: An error occurred: {error}")

def upload_logs(creds, parent, log):
    
    current_month_year = datetime.now().strftime("%b%y")  # Formato "nov24", "dec24", etc.
    log_name_with_date = f"{os.path.splitext(os.path.basename(log))[0]}_{current_month_year}{os.path.splitext(log)[1]}"
    _print(f"Uploading {os.path.basename(log)} as {log_name_with_date} to GDrive:")
    try:
        file_id = upload_logs_core(creds, log, log_name_with_date, parent)
    except Exception as e:
        _print(f"ERROR: Not {os.path.basename(log)} uploaded")
        _print(f"ERROR: {e}")

def delete_uploaded_file(file_gdrive, file, file_path):
    usb_file = os.path.join(USB_PATH, file)
    try:
        if file_gdrive and file_gdrive.get("id"):
            os.remove(usb_file)
            _print(f"File {os.path.basename(file)} removed from USB stick")
            os.remove(file_path)
            _print(f"File {os.path.basename(file)} removed from main folder")
        else:
            _print(f'Comprovation in GDrive failed: {os.path.basename(file_path)} will remain on USB stick')
    except Exception as e:
        _print(f"ERROR: {file}: {e}")
        
if __name__ == "__main__":
    try:
        parent = gdrive_parent()
        creds = log_in_google()
         
        if dtype.lower() == 'rgb':
            path_filetransfer = os.path.join(BASE_PATH, f"{ID}_RGB_filetransfer")
            path_backup = os.path.join(BASE_PATH, f"{ID}_RGB_backup")
            file_type = ".jpg"
            mime_type="image/jpg"
            google_upload(creds, parent)      
        
        elif dtype.lower() == 'tir':
            path_filetransfer = os.path.join(BASE_PATH, f"{ID}_TIR_filetransfer")
            path_backup = os.path.join(BASE_PATH, f"{ID}_TIR_backup")
            file_type = ".zip"
            mime_type="application/zip"
            google_upload(creds, parent)
        
        elif dtype.lower() == 'log':
            file_type = ".log"
            mime_type="text/plain"
            upload_logs(creds, parent, "/home/pi/wittypi/wittyPi.log")
            upload_logs(creds, parent, "/home/pi/wittypi/schedule.log")
            upload_logs(creds, parent, "/home/pi/AI4G.log")

        else:
            _print("ERROR: Provide a valid type of file")
            exit(0)
      
        _print(f"Code successfully completed in {time.time()-start_time:.2f} s")

    except Exception as e:
        _print("ERROR: Main code error")
        _print(f"ERROR: {e}")
