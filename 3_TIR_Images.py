##############################################################################################
# gPhoto2_images: Script to capture and upload DSLR images to Google Drive                   #
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
import os, zipfile
import argparse
from datetime import datetime
import subprocess
import shutil
import glob

parser = argparse.ArgumentParser(description='TIR script to capture thermal images')
parser.add_argument('--id', type=str, required=True, help='ID for the system')
args = parser.parse_args()
BASE_PATH = '/home/pi'

ID = args.id
thermalExe = '/home/pi/scripts/TIRcapture'
path_filetransfer_tir = os.path.join(BASE_PATH, f"{ID}_TIR_filetransfer")
path_backup_tir = os.path.join(BASE_PATH, f"{ID}_TIR_backup")
mount_point = os.path.join(BASE_PATH, "usb_stick")

def _print(message):
    current_time = datetime.now()
    formatted_time = current_time.strftime("[%d/%m/%Y - %H:%M:%S]")
    print(f"{formatted_time} :: TIR_images :: {message}")

def create_subfolder():
    try:
        datetime_folder = datetime.now()
        datetime_name = datetime_folder.strftime("%d%m%y_%H%M")
        path_tir = os.path.join(path_filetransfer_tir, f"{ID}_{datetime_name}_TIR")
        os.makedirs(path_tir, exist_ok = True)
        _print(f'Thermal images will be saved at: {os.path.basename(path_tir)}')
        return datetime_name, path_tir
    except Exception as e:
        _print(f"ERROR creating subfolder: {e}")
        
def capture_thermal_images(path_tir):
    _print('Starting thermal camera data capture')
    time.sleep(1)
    os.system('sudo ' + thermalExe + ' ' + path_tir + '/ ' + str(10) + '  ' + f'{ID}_{datetime_name}_')
    time.sleep(1)
    _print('Thermal images captured')

def create_zip(datetime_name, path_tir):
    try:
        zip_folder = os.path.join(path_filetransfer_tir, f"{ID}_{datetime_name}_TIR.zip")
        _print(f"{os.path.basename(zip_folder)} file will be created")
        with zipfile.ZipFile(zip_folder, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(path_tir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, path_tir)
                    zipf.write(file_path, arcname)
        _print(f'{os.path.basename(zip_folder)} file generated')
    except Exception as e:
        _print(f"ERROR creating ZIP: {e}")

def remove_folder(path_tir):
    try:
        shutil.rmtree(path_tir)
        _print(f'{os.path.basename(path_tir)} removed')
    except Exception as e:
        _print(f"ERROR removing folder {path_tir}: {e}")
    
def sync_folder():
    files = glob.glob(os.path.join(path_filetransfer_tir, "*.zip"))
    try:
        existing_files = set(os.listdir(mount_point))        
        for file in files:
            file_name = os.path.basename(file)
            if file_name not in existing_files:
                shutil.copy2(file, os.path.join(mount_point, os.path.basename(file)))
                _print(f"Synchronising file in USB stick: {os.path.basename(file)}")
                
    except Exception as e:
        _print(f"ERROR: USB Syncronization")
        _print(f"ERROR: {e}")

if __name__ == "__main__":    
    try:   
        datetime_name, path_tir = create_subfolder()
        capture_thermal_images(path_tir)
        create_zip(datetime_name, path_tir)
        remove_folder(path_tir)
        sync_folder()
        _print(f"Code successfully completed in {time.time()-start_time:.2f} s")

    except Exception as e:
        _print("ERROR: Main code error")
        _print(f"ERROR: {e}")