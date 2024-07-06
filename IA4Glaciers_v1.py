##############################################################################################
# IA4Glaciers_v1: Script to capture and upload DSLR images to Google Drive                   #
#                                                                                            #
# Author: Xabier Blanch Gorriz                                                               #
#                                                                                            #
# This script is open-source and licensed under the MIT License.                             #
# Technische Universität Dresden in collaboration with Universitat Politecnica de Catalunya  #
#                                                                                            #
# Copyright (c) XBG 2024                                                        #
##############################################################################################


from time import sleep
import time
start_time = time.time()
from datetime import datetime
from sh import gphoto2 as gp
import os
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

###################################################################
ID = 'GPM01'
num_of_pics = 3
###################################################################

SCOPES = ['https://www.googleapis.com/auth/drive']
path_filetransfer = "/home/pi/" + ID + "_filetransfer"
path_backup = "/home/pi/" + ID + "_backup"

gphoto2_ISO = ["--set-config", "iso=1"]
gphoto2_autodetect = ["--auto-detect"]
gphoto2_capture = ["--capture-image", "-F=" + str(num_of_pics), "-I=3="]
gphoto2_SD_Erase = ["--folder", "/store_00020001/DCIM/100CANON", "-R", "--delete-all-files"]
gphoto2_SD = ["--set-config", "capturetarget=1"]
gphoto2_SD_Transfer = ["--get-all-files"]

def _print(message):
    current_time = datetime.now()
    formatted_time = current_time.strftime("[%d/%m/%Y - %H:%M:%S]")
    print(f"{formatted_time} :: {message}")

def initial():
    _print(f"*** IA4Glaciers_v1 ***")

def create_folders():
    try:
        os.makedirs(path_filetransfer, exist_ok = True)
        _print("Folder " + ID + "_filetransfer created successfully")
        os.makedirs(path_backup, exist_ok = True)
        _print("Folder " + ID + "_backup created successfully")
    except Exception as e:
        _print("ERROR: Folder creation")
        _print(f"ERROR: {e}")

def detect_camera():
    try:
        output = gp(gphoto2_autodetect)
        data_output = output.splitlines()
        model_line = [line for line in data_output if "Canon" in line]
        model = model_line[0].split('  ')[0]
        if model_line:
            _print(f"GPhoto2 - Camera {model} detected")
        else:
            _print(f'Alert! No camera detected')

    except Exception as e:
        _print("ERROR: Camera autodetect not working")
        _print(f"ERROR: {e}")
        return

def time_shutter():
    while True:
        current_second = int(time.time() % 60)
        if current_second == 0:
            _print(f"Time-based shutther triggered")
            try:
                gp(gphoto2_capture)
                _print(f"GPhoto2 - {num_of_pics} images captured")
                sleep(2)
                return
            except Exception as e:
                _print("ERROR: GPhoto2 - Error in capturing photos")
                _print(f"ERROR: {e}")
                return     
            return

def capture_image():
    try:
        detect_camera()
    except Exception as e:
        _print(f"ERROR: Camera detection error")
        _print(f"ERROR: {e}")
        return

    try:
        gp(gphoto2_SD_Erase)
        _print("GPhoto2 - Internal SD card erased")
    except Exception as e:
        _print("ERROR: Error erasing internal SD card")
        _print(f"ERROR: {e}")
        return

    try:
        gp(gphoto2_SD)
        _print("GPhoto2 - Internal SD card selected")
    except Exception as e:
        _print("ERROR: Error internal SD card")
        _print(f"ERROR: {e}")
        return

    try:
        time_shutter()
    except Exception as e:
        _print("ERROR: Time-based shutter")
        _print(f"ERROR: {e}")
        return

    try:
        os.chdir(path_filetransfer)
        gp(gphoto2_SD_Transfer)
        _print(f"GPhoto2 - {num_of_pics} images downloaded")
    except Exception as e:
        _print("ERROR: GPhoto2 - Error in downloading photos")
        _print(f"ERROR: {e}")
        return

def rename_files():
    timestamp = now.strftime("%Y%m%d_%H%M")
    count = 1
    for file in os.listdir(path_filetransfer):
        if len(file) < 15:
            filename = ID + "_" + timestamp + "_" + str(count) + ".jpg"
            os.rename(os.path.join(path_filetransfer, file), os.path.join(path_filetransfer, filename))
            _print(f"File {file} renamed to {filename}")
            count = count + 1

def clear_files():
    date_time = time.time()
    for file in os.listdir(path_backup):
        date_file = os.path.getmtime(os.path.join(path_backup, file))
        if ((now - date_file)/(24*3600))>=20:
            os.unlink(os.path.join(path_backup, file))
            _print(f"File {file} deleted successfully")
        else:
            _print(f"Not backup images to delete")

def clear_error_img():
    for file in os.listdir(path_filetransfer):
        if file.startswith("GPM"):
	        _print(f"File {file} pending to upload")
        else:
	        os.unlink(os.path.join(path_filetransfer, file))
	        _print(f"File {file} corrupted. It has been deleted.")

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

def select_function(now):
    if now.minute in (0,1,2,3,4,5):
        maintenance_mode = False
        _print(f"Maintance mode = False -> {num_of_pics} images will be captured")
    else:
        maintenance_mode = False
        _print(f"Maintance mode = True -> no images will be captured")
        _print(f"Maintance mode - Remember to shutdown the system after the maintance")
    return maintenance_mode

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
    if creds is not None:
        _print("Logging in google API succesfull")
    return creds

def google_upload(creds, output_path, parent):
    try:
        if os.listdir(output_path) != []:
            for file in os.listdir(output_path):
                service = build("drive", "v3", credentials=creds)
                file_metadata = {"parents": parent, "name":  file}
                media = MediaFileUpload(os.path.join(output_path, file), mimetype="image/jpg")
                file_gdrive = (service.files().create(body=file_metadata, media_body=media, fields="id").execute())
                _print(f'File ID: {file_gdrive.get("id")} uploaded')
                if file_gdrive.get("id"):
                    os.replace(os.path.join(output_path,file), os.path.join(path_backup, file))
        else:
            _print("ERROR: No files in the filetransfer folder")
                
    except HttpError as error:
        _print(f'ERROR: GDrive upload failure') 
        _print(f"ERROR: {error}")

if __name__ == "__main__":
    now = datetime.now()
    initial()
    maintenance_mode = select_function(now)
    if not maintenance_mode:
        try:
            output_path = create_folders()
            clear_error_img()
            capture_image()
            rename_files()
            parent = gdrive_parent()
            creds = log_in_google()
            google_upload(creds, path_filetransfer, parent)
            _print(f"Code completed successfully in {time.time()-start_time:.2f} s")
            
        except Exception as e:
            _print("ERROR: Main code error")
            _print(f"ERROR: {e}")