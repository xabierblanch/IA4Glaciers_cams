#!/bin/bash

python3 /home/pi/clear_logs.py

python3 /home/pi/IA4Glaciers_v1.py >> /home/pi/IA4G.log

python3 /home/pi/upload_logs.py

python3 /home/pi/shutdown.py
