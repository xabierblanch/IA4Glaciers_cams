#!/bin/sh

ID="GPM_Dresden"

log_file="/home/pi/AI4G.log"

thermal=true

internet=false
capture_images=false
maintenance=false
rgb=false 

get_current_time() {
    echo $(date +"[%d/%m/%Y - %H:%M:%S]")
}

if [ -d "/home/pi/AI4G_env/bin" ]; then
    . /home/pi/AI4G_env/bin/activate
else
    echo "$(get_current_time) :: ERROR :: Virtual environment not found. Exiting." >> "$log_file"
    exit 1
fi

sleep 4 #Wait time until WittyPi set the right time to the RasPi

current_time=$(date +"%d/%m/%Y - %H:%M:%S")
current_hour=$(date +"%H")
current_minute=$(date +"%M")

#current_minute=$(date +"%M")
echo "$(get_current_time) :: ******************************************" >> "$log_file"
echo "$(get_current_time) :: IA4Glaciers :: New instance started: ID = $ID" >> "$log_file"

TIME_OF_DAY=$(python3 /home/pi/scripts/0_day_night.py)

if [ "$TIME_OF_DAY" = "night" ]; then
    echo "$(get_current_time) :: IA4Glaciers :: Current time ($current_hour UTC) is in night range" >> "$log_file"
    if [ "$thermal" = false ]; then
        echo "$(get_current_time) :: IA4Glaciers :: Night time - TIR Camera not avilable, executing shutdown..." >> "$log_file"
        python3 /home/pi/scripts/5_shutdown.py --force >> "$log_file"
    else
        echo "$(get_current_time) :: IA4Glaciers :: Night time - TIR Camera available, skipping shutdown" >> "$log_file"
		rgb=false
    fi
else
    echo "$(get_current_time) :: IA4Glaciers :: Current time ($current_hour UTC) is in daylight range" >> "$log_file"
	rgb=true
fi

if [ "$current_minute" = "00" ] || [ "$current_minute" = "01" ] || [ "$current_minute" = "02" ] || [ "$current_minute" = "03" ] || [ "$current_minute" = "30" ] || [ "$current_minute" = "31" ] || [ "$current_minute" = "32" ] || [ "$current_minute" = "33" ]; then 
    echo "$(get_current_time) :: IA4Glaciers :: Started at RGB minute: Images will be taken" >> "$log_file"
	capture_images=true
else
    echo "$(get_current_time) :: IA4Glaciers :: Started at a maintenance minute. No images will be captured" >> "$log_file"
	maintenance=true
fi

sleep 1

python3 /home/pi/scripts/1_maintenance.py --id="$ID" --backup=30 >> "$log_file"

sleep 1

if [ "$capture_images" = true ] && [ "$rgb" = true ]; then
	echo "$(get_current_time) :: IA4Glaciers :: RGB Camera module active" >> "$log_file"
    python3 /home/pi/scripts/2_RGB_images.py --id="$ID" --num=1 >> "$log_file"
fi

if [ "$capture_images" = true ] && [ "$thermal" = true ]; then
	echo "$(get_current_time) :: IA4Glaciers :: Thermal Camera module active" >> "$log_file"
	python3 /home/pi/scripts/3_TIR_Images.py --id="$ID" >> "$log_file"
fi

if ping -q -c 1 -W 1 google.com > /dev/null || ping -q -c 1 -W 1 cloudflare.com > /dev/null; then
	echo "$(get_current_time) :: IA4Glaciers :: Internet connection detected - GDrive scripts will be executed" >> "$log_file"
	internet=true
else
	echo "$(get_current_time) :: IA4Glaciers :: No internet connection - GDrive scripts will be skipped" >> "$log_file"
fi

if [ "$maintenance" = true ]; then
	echo "$(get_current_time) :: IA4Glaciers :: System is in uploading mode - Waiting up to 180 seconds for internet connection" >> "$log_file"
	end_wait=$(( $(date +%s) + 180))
	while [ $(date +%s) -lt $end_wait ]; do
		if ping -q -c 1 -W 1 google.com > /dev/null || ping -q -c 1 -W 1 cloudflare.com > /dev/null; then
			internet=true
			echo "$(get_current_time) :: IA4Glaciers :: Internet connection detected" >> "$log_file"
			break
		fi
	done

	if [ "$internet" = false ]; then
		echo "$(get_current_time) :: IA4Glaciers :: No internet connection after 180 seconds - GDrive scripts will be skipped" >> "$log_file"
	fi
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

if [ "$maintenance" = true ]; then
	echo "$(get_current_time) :: IA4Glaciers :: Maintenance mode allowed - Waiting 1.5 minutes for a flag file" >> "$log_file"
	sleep 90
	python3 /home/pi/scripts/5_shutdown.py >> "$log_file"
else
	echo "$(get_current_time) :: IA4Glaciers :: Maintenance mode not allowed - Force shutdown" >> "$log_file"
	python3 /home/pi/scripts/5_shutdown.py >> "$log_file"
	#python3 /home/pi/scripts/5_shutdown.py --force >> "$log_file"
fi

#touch /home/pi/maintenance_mode.flag