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
from datetime import datetime
import glob
from sh import gphoto2 as gp
import RPi.GPIO as GPIO
import subprocess
import os
import argparse
import shutil

parser = argparse.ArgumentParser(description='Maintenance script to clean and remove files.')
parser.add_argument('--id', type=str, required=True, help='ID for the system')
parser.add_argument('--num', type=int, default=2, help='Number of burst images')
args = parser.parse_args()
BASE_PATH = '/home/pi'
ID = args.id
num_of_pics = args.num

path_filetransfer_rgb = os.path.join(BASE_PATH, f"{ID}_RGB_filetransfer")
path_backup_rgb = os.path.join(BASE_PATH, f"{ID}_RGB_backup")
mount_point = os.path.join(BASE_PATH, "usb_stick")

gphoto2_ISO = ["--set-config", "iso=1"]
#gphoto2_focus = ["--set-config", "autofocusdrive=1"]
gphoto2_autodetect = ["--summary"]
gphoto2_capture = ["--capture-image", "-F=" + str(num_of_pics), "-I=3="]
gphoto2_SD_Erase = ["--folder", "/store_00020001/DCIM/100CANON", "-R", "--delete-all-files"]
gphoto2_SD = ["--set-config", "capturetarget=1"]
gphoto2_SD_Transfer = ["--get-all-files"]

def _print(message):
    current_time = datetime.now()
    formatted_time = current_time.strftime("[%d/%m/%Y - %H:%M:%S]")
    print(f"{formatted_time} :: RGB_images :: {message}")

def control_relay(mode):
    try:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(21, GPIO.OUT)
        if mode == "up":
            GPIO.output(21, GPIO.HIGH)
            _print("Camera relay activated succesfully")
            time.sleep(4)
        if mode == "down":
            time.sleep(1)
            GPIO.output(21, GPIO.LOW)
            _print("Camera relay deactivated succesfully")     
            #GPIO.cleanup()
    except Exception as e:
        _print("ERROR: Camera relay")
        _print(f"ERROR: {e}")    

def detect_camera():
    try:
        output = gp(gphoto2_autodetect)
        data_output = output.splitlines()
        model_line = [line for line in data_output if "Model:" in line][0]
        if model_line:
            _print(f"GPhoto2 - Camera {model_line} detected")
        else:
            _print(f'Alert! No camera detected')

    except Exception as e:
        _print("ERROR: Camera autodetect not working")
        return

def time_shutter():
    while True:
        current_second = int(time.time() % 60)
        if current_second == 35:
            _print(f"Time-based shutther triggered")
            try:
                gp(gphoto2_capture)
                _print(f"GPhoto2 - {num_of_pics} images captured")
                time.sleep(2)
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
        return

    try:
        time.sleep(1)
        gp(gphoto2_SD_Erase)
        _print("GPhoto2 - Internal SD card erased")
    except Exception as e:
        _print("ERROR: Error erasing internal SD card")
        return

    try:
        time.sleep(1)
        gp(gphoto2_SD)
        _print("GPhoto2 - Internal SD card selected")
    except Exception as e:
        _print("ERROR: Error internal SD card")
        _print(f"ERROR: {e}")
        return
        
    try:
        time.sleep(1)
        time_shutter()
    except Exception as e:
        _print("ERROR: Time-based shutter")
        _print(f"ERROR: {e}")
        return

    try:
        os.chdir(path_filetransfer_rgb)
        time.sleep(1)
        gp(gphoto2_SD_Transfer)
        _print(f"GPhoto2 - {num_of_pics} images downloaded from the camera")
    except Exception as e:
        _print("ERROR: GPhoto2 - Error in downloading photos")
        _print(f"ERROR: {e}")
        return

def rename_files():
    now = datetime.now()
    timestamp = now.strftime("%y%m%d_%H%M")
    count = 1
    for file in os.listdir(path_filetransfer_rgb):
        if len(file) < 15:
            filename = ID + "_" + timestamp + "_" + str(count) + ".jpg"
            os.rename(os.path.join(path_filetransfer_rgb, file), os.path.join(path_filetransfer_rgb, filename))
            _print(f"File {file} renamed to {filename}")
            count = count + 1

def sync_folder():
    files = glob.glob(os.path.join(path_filetransfer_rgb, "*.jpg"))
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
        control_relay("up")
        capture_image()
        control_relay("down")
        rename_files()
        sync_folder()
        _print(f"Code successfully completed in {time.time()-start_time:.2f} s")
            
    except Exception as e:
        _print("ERROR: Main code error")
        _print(f"ERROR: {e}")
