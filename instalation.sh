#!/bin/sh

sudo apt update

cd /home/pi

sudo apt install -y gphoto2
sudo apt install -y python3-pip

wget -O /home/pi/install.sh https://www.uugear.com/repo/WittyPi4/install.sh
sudo sh /home/pi/install.sh
rm /home/pi/install.sh
sudo update-rc.d uwi remove
sudo rm /etc/init.d/uwi
sudo rm -r ~/uwi
sudo apt install python3-venv

python3 -m venv AI4G_env
. /home/pi/AI4G_env/bin/activate
pip install --upgrade RPi.GPIO
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
pip install --upgrade sh

chmod +x /home/pi/scripts/IA4Glaciers.sh

sudo apt install libopencv-dev

#copy file (WinSCP)

sudo chmod u+x i3system_sdk_aarch64.run
sudo ./i3system_sdk_aarch64.run
g++ te_ev2_ai4g.cpp -I/usr/include/opencv4 -L/usr/lib -lopencv_core -lopencv_imgcodecs -I/usr/local/include/i3system -L/usr/local/lib -li3system_te_64 -o thermalCapture
echo "/usr/local/lib" | sudo tee /etc/ld.so.conf.d/usr_local_lib.conf
sudo ldconfig

#todo
#modify wittypi scripts

echo "****************"
echo "Modify crontab:"
echo "crontab -e"
echo "@reboot sh /home/pi/scripts/AI4Glaciers.sh"
echo "****************"
echo "Installation completed"
