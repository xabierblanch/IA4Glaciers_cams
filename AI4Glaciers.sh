#!/bin/sh

ID="GPM_Dresden"

log_file="/home/pi/AI4G.log"

internet=false
capture_images=false
thermal=true

if [ -d "/home/pi/AI4G_env/bin" ]; then
    . /home/pi/AI4G_env/bin/activate
else
    echo "$(get_current_time) :: ERROR: Virtual environment not found. Exiting." >> "$log_file"
    exit 1
fi

sleep 5 #Wait time until WittyPi set the right time to the RasPi

current_time=$(date +"%d/%m/%Y - %H:%M:%S")
current_hour=$(date +"%H")

get_current_time() {
    echo $(date +"[%d/%m/%Y - %H:%M:%S]")
}

#current_minute=$(date +"%M")
echo "$(get_current_time) :: ******************************************" >> "$log_file"
echo "$(get_current_time) :: IA4Glaciers: New instance started: ID = $ID" >> "$log_file"

if [ "$current_hour" -ge 6 ] && [ "$current_hour" -le 18 ]; then
#if [ "$current_hour" -ge 6 ] && [ "$current_hour" -le 18 ] && [ "$current_minute" -ge 0 ] && [ "$current_minute" -le 5 ]; then
    capture_images=true
    echo "$(get_current_time) :: IA4Glaciers: Current time ($current_hour UTC) is in the allowed range (6h to 18h) - gPhoto2 script will be executed" >> "$log_file"
else
    echo "$(get_current_time) :: IA4Glaciers: Current time ($current_hour UTC) is out of range (6h to 18h) - gPhoto2 script will be skipped" >> "$log_file"
fi

sleep 1

python3 /home/pi/scripts/1_maintenance.py --id="$ID" --backup=30 >> "$log_file"

sleep 1

if [ "$capture_images" = true ]; then
    python3 /home/pi/scripts/2_RGB_images.py --id="$ID" --num=1 >> "$log_file"
	echo "$(get_current_time) :: IA4Glaciers: System is in capture mode - No internet connection expected" >> "$log_file"
	if ping -q -c 1 -W 1 google.com > /dev/null; then
		echo "$(get_current_time) :: IA4Glaciers: Internet connection detected - GDrive scripts will be executed" >> "$log_file"
		internet=true
	else
		echo "$(get_current_time) :: IA4Glaciers: No internet connection - GDrive scripts will be skipped" >> "$log_file"
    fi

else
	echo "$(get_current_time) :: IA4Glaciers: System is in uploading mode - Waiting up to 180 seconds for internet connection" >> "$log_file"
    end_wait=$(( $(date +%s) + 180))
    while [ $(date +%s) -lt $end_wait ]; do
        if ping -q -c 1 -W 1 google.com > /dev/null || ping -q -c 1 -W 1 cloudflare.com > /dev/null; then
            internet=true
            break
        fi
        sleep 2
    done

    if [ "$internet" = true ]; then
        echo "$(get_current_time) :: IA4Glaciers: Internet connection detected - GDrive scripts will be executed" >> "$log_file"
    else
        echo "$(get_current_time) :: IA4Glaciers: No internet connection after 180 seconds - GDrive scripts will be skipped" >> "$log_file"
    fi
fi

if [ "$thermal" = true ]; then
	echo "$(get_current_time) :: IA4Glaciers: Thermal Camera module active" >> "$log_file"
	python3 /home/pi/scripts/3_TIR_Images.py --id="$ID" >> "$log_file"
fi

sleep 1

if [ "$internet" = true ]; then
	python3 /home/pi/scripts/4_GDrive.py --id="$ID" --filetype=RGB >> "$log_file"
        sleep 1
	if [ "$thermal" = true ]; then
		python3 /home/pi/scripts/4_GDrive.py --id="$ID" --filetype=TIR >> "$log_file"
	fi
	sleep 1
	python3 /home/pi/scripts/4_GDrive.py --id="$ID" --filetype=LOG >> "$log_file"
fi

sleep 1

if [ "$capture_images" = true ]; then
	echo "$(get_current_time) :: IA4Glaciers: Maintenance mode not allowed - Force shutdown" >> "$log_file"
	#python3 /home/pi/scripts/5_shutdown.py --force >> "$log_file"
	python3 /home/pi/scripts/5_shutdown.py >> "$log_file"
else
	echo "$(get_current_time) :: IA4Glaciers: Maintenance mode allowed - Waiting 2 minutes for a flag file" >> "$log_file"
	sleep 120
	python3 /home/pi/scripts/5_shutdown.py >> "$log_file"
fi

#touch /home/pi/maintenance_mode.flag
