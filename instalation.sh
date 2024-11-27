#!/bin/sh

# Update and upgrade the system to ensure we have the latest package information and upgrades
echo "Updating and upgrading the system..."
sudo apt update && sudo apt upgrade -y

# Define base directory and scripts directory for easier path management
BASE_DIR="$HOME"
SCRIPTS_DIR="$BASE_DIR/scripts"

# Change to the base directory
echo "Changing directory to $BASE_DIR..."
cd $BASE_DIR

# Install necessary packages: gphoto2 (camera control), python3-pip, python3-venv (for Python virtual environments), 
# libopencv-dev (OpenCV for computer vision tasks), and build-essential (for compiling software)
echo "Installing required packages..."
sudo apt install -y gphoto2
sudo apt install -y python3-pip
sudo apt install -y python3-venv
sudo apt install -y libopencv-dev
sudo apt install -y build-essential

# Download the Witty Pi 4 installation script
echo "Downloading Witty Pi installation script..."
if ! wget -O $HOME/install.sh https://www.uugear.com/repo/WittyPi4/install.sh; then
    echo "Error downloading install.sh. Aborting."
    exit 1
fi

# Run the Witty Pi installation script and remove it after installation
echo "Running Witty Pi installation script..."
sudo sh $HOME/install.sh
rm $HOME/install.sh

# Remove old Witty Pi startup configurations and files
echo "Cleaning up old Witty Pi configurations..."
sudo update-rc.d uwi remove
sudo rm /etc/init.d/uwi
sudo rm -r ~/uwi

# Create a Python virtual environment for the project
echo "Creating Python virtual environment..."
python3 -m venv AI4G_env

# Activate the Python virtual environment
echo "Activating the Python virtual environment..."
. /home/pi/AI4G_env/bin/activate

# Upgrade necessary Python libraries: RPi.GPIO, Google API client libraries, and sh
echo "Upgrading required Python libraries..."
pip install --upgrade RPi.GPIO
pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
pip install --upgrade sh

# Check if the IA4Glaciers.sh script exists in the directory and give it executable permissions
echo "Checking if IA4Glaciers.sh exists..."
if [ -f $SCRIPTS_DIR/IA4Glaciers.sh ]; then
    echo "Setting executable permissions for IA4Glaciers.sh..."
    chmod +x $SCRIPTS_DIR/IA4Glaciers.sh
else
    echo "The script IA4Glaciers.sh does not exist in $SCRIPTS_DIR. Please check."
fi

# Download the i3system SDK installer and give it executable permissions
echo "Downloading i3system SDK installer..."
wget https://github.com/xabierblanch/IA4Glaciers_cams/raw/refs/heads/main/i3system_sdk_aarch64.run
echo "Making i3system SDK installer executable..."
sudo chmod u+x i3system_sdk_aarch64.run
echo "Running i3system SDK installer..."
sudo ./i3system_sdk_aarch64.run

# Download the C++ source file for thermal image capture
echo "Downloading te_ev2_ai4g.cpp source file..."
wget -O $SCRIPTS_DIR/te_ev2_ai4g.cpp https://github.com/xabierblanch/IA4Glaciers_cams/raw/refs/heads/main/te_ev2_ai4g.cpp

# Change to the scripts directory and compile the C++ source code
echo "Compiling C++ source code for thermal image capture..."
cd $SCRIPTS_DIR
g++ te_ev2_ai4g.cpp -I/usr/include/opencv4 -L/usr/lib -lopencv_core -lopencv_imgcodecs -I/usr/local/include/i3system -L/usr/local/lib -li3system_te_64 -o TIRcapture

# Update the system’s library cache for i3system libraries
echo "Updating system library cache..."
echo "/usr/local/lib" | sudo tee /etc/ld.so.conf.d/usr_local_lib.conf
sudo ldconfig

# Remove the SDK installer after successful installation
echo "Cleaning up the i3system SDK installer..."
sudo rm -r /home/pi/i3system_sdk_aarch64.run

# Go back to the base directory
echo "Returning to the base directory..."
cd $BASE_DIR

# Download the Python scripts required for the project
echo "Downloading Python scripts..."
wget -O $SCRIPTS_DIR/1_maintenance.py https://github.com/xabierblanch/IA4Glaciers_cams/raw/refs/heads/main/1_maintenance.py
wget -O $SCRIPTS_DIR/2_RGB_images.py https://github.com/xabierblanch/IA4Glaciers_cams/raw/refs/heads/main/2_RGB_images.py
wget -O $SCRIPTS_DIR/3_TIR_Images.py https://github.com/xabierblanch/IA4Glaciers_cams/raw/refs/heads/main/3_TIR_Images.py
wget -O $SCRIPTS_DIR/4_GDrive.py https://github.com/xabierblanch/IA4Glaciers_cams/raw/refs/heads/main/4_GDrive.py
wget -O $SCRIPTS_DIR/5_shutdown.py https://github.com/xabierblanch/IA4Glaciers_cams/raw/refs/heads/main/5_shutdown.py

# Download additional files related to Witty Pi scheduling
echo "Downloading Witty Pi scheduling files..."
wget -O $BASE_DIR/wittypi/schedules/IA4G.wpi https://github.com/xabierblanch/IA4Glaciers_cams/raw/refs/heads/main/IA4G.wpi

# Restore the crontab from the backup file and enable the cron service
echo "Restoring crontab from backup and enabling cron service..."
wget -O $SCRIPTS_DIR/crontab_backup.txt https://github.com/xabierblanch/IA4Glaciers_cams/raw/refs/heads/main/crontab_backup.txt
crontab crontab_backup.txt
sudo systemctl enable --now cron

# Clean up the crontab backup file
echo "Cleaning up crontab backup file..."
sudo rm -r $SCRIPTS_DIR/crontab_backup.txt

# Check if the cron service is active and display a warning if it failed to start
echo "Checking cron service status..."
sudo systemctl is-active --quiet cron || echo "Warning: The cron service could not be activated."

# Download Google Drive token and shutdown scripts
echo "Downloading Google Drive token and shutdown scripts..."
wget -O $SCRIPTS_DIR/token.json https://github.com/xabierblanch/IA4Glaciers_cams/raw/refs/heads/main/token.json
wget -O $SCRIPTS_DIR/sh_shutdown.sh https://github.com/xabierblanch/IA4Glaciers_cams/raw/refs/heads/main/sh_shutdown.sh

# Clean up unnecessary packages and temporary files to free up disk space
echo "Removing unnecessary packages and cleaning up temporary files..."
sudo apt autoremove -y
sudo apt clean

# Final message indicating the installation is complete
echo "Installation completed successfully!"

