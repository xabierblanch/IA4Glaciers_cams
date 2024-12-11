##############################################################################################
# Maintenance: Script to clean and remove files to maintance the system                     #
#                                                                                            #
# Author: Xabier Blanch Gorriz                                                               #
#                                                                                            #
# This script is open-source and licensed under the MIT License.                             #
# Technische UniversitÃ¤t Dresden in collaboration with Universitat Politecnica de Catalunya #
#                                                                                            #
# Copyright (c) XBG 2024                                                                     #
##############################################################################################

import time
start_time = time.time()
import os
from datetime import datetime
import argparse
import glob
import shutil
import subprocess

parser = argparse.ArgumentParser(description='Maintenance script to clean and remove files.')
parser.add_argument('--id', type=str, required=True, help='ID for the system')
parser.add_argument('--backup', type=int, default=5, help='Threshold in days for backup file deletion')
parser.add_argument('--thermal', type=str, default='false', help='Thermal camera?')
args = parser.parse_args()
BASE_PATH = '/home/pi'

ID = args.id
day_threshold = args.backup
thermal_arg = args.thermal
path_filetransfer_rgb = os.path.join(BASE_PATH, f"{ID}_RGB_filetransfer")
path_filetransfer_temp = os.path.join(BASE_PATH, f"{ID}_TEMP_filetransfer")
path_backup_rgb = os.path.join(BASE_PATH, f"{ID}_RGB_backup")
path_filetransfer_tir = os.path.join(BASE_PATH, f"{ID}_TIR_filetransfer")
path_backup_tir = os.path.join(BASE_PATH, f"{ID}_TIR_backup")
path_logs_backup = os.path.join(BASE_PATH, f"{ID}_logs_backup")
mount_point = os.path.join(BASE_PATH, "usb_stick")

def _print(message):
    current_time = datetime.now()
    formatted_time = current_time.strftime("[%d/%m/%Y - %H:%M:%S]")
    print(f"{formatted_time} :: Maintenance :: {message}")
    
def delete_flags():
    flags = glob.glob("/home/pi/*.flag")
    if flags:
        for flag in flags:
            _print(f"Flag file {os.path.basename(flag)} detected")
            os.remove(flag)
            _print(f"Flags: {os.path.basename(flag)} removed from the system")
    else:
        _print("No flag file detected")
        
def create_folders(path):
    try:
        os.makedirs(path, exist_ok = True)
        _print(f"Folder {os.path.basename(path)} created successfully")
    except Exception as e:
        _print(f"ERROR creating folder {os.path.basename(path)}: {e}")   
    
def list_clean_img(path):
    if not os.path.exists(path):
        _print(f"ERROR: {path} does not exist.")
        return
        
    if not any(os.scandir(path)):
        _print(f'FileTransfer: No images in the {os.path.basename(path)}')
    else:
        for file in os.listdir(path):
            if file.startswith("GPM"):
                #_print(f"FileTransfer: File {file} from {os.path.basename(path)} pending to upload")
                return
            else:
                os.unlink(os.path.join(path, file))
                _print(f"FileTransfer: File {file} in {os.path.basename(path)} is corrupted. It has been deleted")

def check_month():
    try:
        current_datestamp = datetime.now().strftime("%b%y")

        if os.path.exists("/home/pi/datestamp"):
            with open("/home/pi/datestamp", "r") as f:
                datestamp = f.read().strip()
            _print(f"Last datestamp found: {datestamp}")

        else:
            _print("File /home/pi/datestamp does not exist. Creating it with the current month")
            with open("/home/pi/datestamp", "w") as f:
                f.write(current_datestamp)
            datestamp = current_datestamp

    except Exception as e:
        _print(f"ERROR checking the datestamp")
        _print(f"ERROR: {e}")

    return datestamp, current_datestamp

def check_mount(directory):
    count = -1
    with open('/proc/mounts', 'r') as mounts:
        if mount_point in mounts.read():
            try:
                count = sum(len(files) for _, _, files in os.walk(directory))
            except:
                count = -999
            _print(f"USB mounted correctly in {mount_point} - {count} files stored")
        else:
            _print(f'USB not mounted correctly')  
    return count

def clean_old_files(path):
    if not os.path.exists(path):
        _print(f"ERROR: {path} does not exist.")
        return
        
    if not any(os.scandir(path)):
        _print(f'Clean Folder: No files in the {os.path.basename(path)}')   
    else:
        _print(f'Clean Folder: There are {len(os.listdir(path))} images in {os.path.basename(path)}')
        date_time = time.time()
        deleted_images = 0
        for file in os.listdir(path):
            date_file = os.path.getmtime(os.path.join(path, file))
            if ((date_time - date_file)/(24*3600))>= day_threshold:
                try:
                    os.unlink(os.path.join(path, file))
                    _print(f"Clean Folder: File {file} deleted successfully")
                except Exception as e:
                    _print(f"ERROR deleting {file}: {e}")
                deleted_images = deleted_images + 1
        if deleted_images == 0:
            _print(f'Clean Folder: No files older than {day_threshold} days. No folder cleanning')
        else:
            _print(f'Clean Folder: {deleted_images} images deleted because are older than {day_threshold}')

def backup_and_clear_log(log_path, datestamp, current_datestamp):
    try:
        if current_datestamp != datestamp:
            _print(f"Logs: New month detected: {current_datestamp}. Starting {log_path} log backup")
            log_name_with_date = f"{os.path.splitext(os.path.basename(log_path))[0]}_{current_datestamp}{os.path.splitext(log_path)[1]}"
            backup_path = os.path.join(path_logs_backup, log_name_with_date)
            try:
                shutil.copy(log_path, backup_path)
                _print(f"Logs: Backup done. Removing source log file to restart the content")
                subprocess.check_call(['sudo', 'rm', log_path])
                _print(f"Logs: {os.path.basename(log_path)} has been deleted")
            except Exception as e:
                _print(f"ERROR: Failed to back up log file {log_path}. {e}")
                
            with open("/home/pi/datestamp", "w") as f:
                f.write(current_datestamp)

    except Exception as e:
        _print(f"ERROR with {os.path.basename(log_path)}")
        _print(f"ERROR: {e}")

def mount_usb():
    try:      
        os.makedirs(mount_point, exist_ok=True)
        output = subprocess.check_output("lsblk -o NAME,TYPE -nr | grep '^sd'", shell=True)
        device = output.decode().split("\n")[1].split(" ")[0]
        if device:
            try:
                #subprocess.run(['sudo', 'systemctl', 'daemon-reload'])
                subprocess.check_call(['sudo', 'mount', '-o', 'uid=pi,gid=pi', f'/dev/{device}', mount_point])
                #subprocess.check_call(['sudo', 'mount', mount_point])
                return device, mount_point
                
            except Exception as e:
                _print(f"ERROR: USB {device}")
                _print(f"ERROR: {e}")
        else:
            _print(f"No USB stick detected")
            
    except Exception as e:
        _print(f"ERROR: USB {device}")
        _print(f"ERROR: {e}")

if __name__ == "__main__":   
    try:
        try:
            device, mount_point = mount_usb()
        except:
            _print("ERROR: USB not mounted")
        check_mount(mount_point)                
        create_folders(path_filetransfer_rgb)
        create_folders(path_logs_backup)      
        list_clean_img(path_filetransfer_rgb)
        clean_old_files(path_filetransfer_rgb)

        if thermal_arg.lower() == 'true':
            _print('Thermal Camera module enabled: TIR Actions will be performed')
            create_folders(path_filetransfer_tir)
            create_folders(path_filetransfer_temp)
            list_clean_img(path_filetransfer_tir)
            clean_old_files(path_filetransfer_tir)
            clean_old_files(path_filetransfer_temp)
            
        delete_flags()
        datestamp, current_datestamp = check_month()
        backup_and_clear_log('/home/pi/AI4G.log', datestamp, current_datestamp)
        backup_and_clear_log('/home/pi/wittypi/wittyPi.log', datestamp, current_datestamp)
        backup_and_clear_log('/home/pi/wittypi/schedule.log', datestamp, current_datestamp)

        _print(f"Code successfully completed in {time.time()-start_time:.2f} s")

    except Exception as e:
        _print("ERROR: Main code error")
        _print(f"ERROR: {e}")
