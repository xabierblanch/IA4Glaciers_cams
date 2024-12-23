##############################################################################################
# shutdown: Script to shutdown the system                                                    #
#                                                                                            #
# Author: Xabier Blanch Gorriz                                                               #
#                                                                                            #
# This script is open-source and licensed under the MIT License.                             #
# Technische Universität Dresden in collaboration with Universitat Politecnica de Catalunya  #
#                                                                                            #
# Copyright (c) XBG 2024                                                                     #
##############################################################################################

from datetime import datetime, timedelta
import RPi.GPIO as GPIO
import os
import argparse
import time
import subprocess
FLAG_FILE = "/home/pi/1.flag"

def unmount_usb(mount_point):
    try:
        subprocess.run(['sudo', 'umount', mount_point], check=True)
        print(f"Successfully unmounted the USB from {mount_point}")
    except subprocess.CalledProcessError as e:
        print(f"Error while unmounting the USB: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def _print(message):
    current_time = datetime.now()
    formatted_time = current_time.strftime("[%d/%m/%Y - %H:%M:%S]")
    print(f"{formatted_time} :: Shutdown :: {message}")

def is_maintenance_mode():
    if os.path.exists(FLAG_FILE):
        current_time = datetime.now()
        shutdown_time = current_time + timedelta(seconds=1800)
        shutdown_time_str = shutdown_time.strftime("%H:%M")
        _print(f"Flag file detected. The system will be on for a maximum of 30 minutes. Shutdown scheduled at {shutdown_time_str})" )
    else:
        _print("No flag file detected. The system will shutdown inmediatly" )
    return os.path.exists(FLAG_FILE)
    
def shutdown():
    try:
        _print("Shutdown command recieved")
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(4, GPIO.OUT)
        GPIO.output(4, GPIO.LOW)
        _print("GPIO Shutdown executed successfully")
    except Exception as e:
        _print(f"ERROR: executing GPIO commands: {e}")
    finally:
        GPIO.cleanup()
        
if __name__ == "__main__":
    now = datetime.now()
    parser = argparse.ArgumentParser(description="Shutdown script with optional force mode")
    parser.add_argument("--force", action="store_true", help="Force shutdown even in maintenance mode")
    args = parser.parse_args()
    unmount_usb('/home/pi/usb_stick')

    if args.force:
        _print("--force command recieved. Shutdown will be forced now")
        shutdown()
    
    else:
        maintenance_mode = is_maintenance_mode()
        if maintenance_mode:
            time.sleep(1800)
            _print("End of maintenance mode - Flag file removed and system shutdown initiated" )
            try:
                os.remove(FLAG_FILE)    
            except:
                _print("ERROR:No flag file")                
            shutdown()
        else:
            shutdown()
        
#touch /home/pi/1.flag
