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
import os, zipfile, sys, csv
import argparse
from datetime import datetime
import subprocess
import shutil
import glob
from pathlib import Path

parser = argparse.ArgumentParser(description='TIR script to capture thermal images')
parser.add_argument('--id', type=str, required=True, help='ID for the system')
args = parser.parse_args()
BASE_PATH = '/home/pi'

ID = args.id
thermalExe = '/home/pi/scripts/TIRcapture'
path_filetransfer_tir = os.path.join(BASE_PATH, f"{ID}_TIR_filetransfer")
mount_point = os.path.join(BASE_PATH, "usb_stick")
path_filetransfer_temp = os.path.join(BASE_PATH, f"{ID}_TEMP_filetransfer")
ite=3

def _print(message):
    current_time = datetime.now()
    formatted_time = current_time.strftime("[%d/%m/%Y - %H:%M:%S]")
    print(f"{formatted_time} :: TIR_images :: {message}")

def __print(message):
    current_time = datetime.now()
    formatted_time = current_time.strftime("[%d/%m/%Y - %H:%M:%S]")
    print(f"{formatted_time} :: TEMP_sensor :: {message}")

def create_subfolder():
    try:
        datetime_folder = datetime.now()
        datetime_name = datetime_folder.strftime("%d%m%y_%H%M")
        path_tir = os.path.join(path_filetransfer_tir, f"{ID}_{datetime_name}_TIR")
        os.makedirs(path_tir, exist_ok = True)
        _print(f'Thermal images will be saved at: {os.path.basename(path_tir)}')
        return datetime_name, path_tir, datetime_folder
    except Exception as e:
        _print(f"ERROR creating subfolder: {e}")
        
def capture_thermal_images(path_tir):
    try:
        os.system('sudo ' + thermalExe + ' ' + path_tir + '/ ' + str(4) + '  ' + f'{ID}_{datetime_name}_')
    except:
        __print('ERROR executing C++ code')

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
    
def sync_folder(path_filetransfer_tir, file_type):
    files = glob.glob(os.path.join(path_filetransfer_tir, f"*{file_type}"))
    try:
        existing_files = set(os.listdir(mount_point))        
        for file in files:
            file_name = os.path.basename(file)
            if file_name not in existing_files:
                shutil.copy2(file, os.path.join(mount_point, os.path.basename(file)))
                _print(f"Synchronising {file_type} file in USB drive: {os.path.basename(file)}")
                
    except Exception as e:
        _print(f"ERROR: USB Syncronization")
        _print(f"ERROR: {e}")

def temperatureDS18B20(deviceName):
    id = deviceName.split("/")[5]
    try:
        f = open(sensor, "r")
        data = f.read()
        f.close()
        if "YES" in data:
            (discard, sep, reading) = data.partition(' t=')
            tempVal = float(reading) / 1000.0
        else:
            tempVal = 999.9
    except Exception as e:
        print(e)
        pass

    return id, tempVal

def writeToFile(path_filetransfer_temp, datetime_folder): 
    try:
        timestamp = datetime_folder.strftime("%Y%m%d_%H%M")
        filename = ID + "_" + timestamp + "_Temp.txt"
        writeTemp = open(os.path.join(path_filetransfer_temp, filename), 'w')
        writer = csv.writer(writeTemp)
        writer.writerow(['date', 'device', 'temperature'])
        writeTemp.flush()
        __print(f"Temperature file {filename} created in {os.path.basename(path_filetransfer_temp)} folder")
    except:
        __print(f"ERROR: Temperature file can't be created")
    return writer, writeTemp, filename

if __name__ == "__main__":    
    try:   
        datetime_name, path_tir, datetime_folder = create_subfolder()
        capture_thermal_images(path_tir)     
        writer, writeTemp, filename = writeToFile(path_filetransfer_temp, datetime_folder)       
        for sensor in glob.glob("/sys/bus/w1/devices/28-*/w1_slave"):
            __print(f"Temp sensor {Path(sensor).parent.name} identified: Measuring temperatures")
            try:
                for i in range(ite):
                    now = datetime.now()
                    timestamp_txt = now.strftime("%Y-%m-%d_%H:%M:%S")
                    device, temperature = temperatureDS18B20(sensor)
                    writer.writerow([timestamp_txt, device, temperature])
                    writeTemp.flush()
                    time.sleep(1)
            except Exception as e:
                print(e)
                pass
        __print(f"Temperatures measured and file {filename} saved")
        create_zip(datetime_name, path_tir)
        remove_folder(path_tir)
        sync_folder(path_filetransfer_tir, ".zip")
        sync_folder(path_filetransfer_temp, ".txt")
        _print(f"Code successfully completed in {time.time()-start_time:.2f} s")

    except Exception as e:
        _print("ERROR: Main code error")
        _print(f"ERROR: {e}")
