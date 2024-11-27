# IA4Glaciers Installation Guide
Follow the steps below to set up the IA4Glaciers project on your Raspberry Pi.
Create an RPi image:
- [ ] WI-FI enabled
- [ ] SSH enabled


### 1. Download the Installation Script
To begin the installation process, download the installation script by running the following command:

```bash
wget https://github.com/xabierblanch/IA4Glaciers_cams/raw/refs/heads/main/instalation.sh
```
```bash
sh installation.sh
```

### 2. Modify the ID of the system
```bash
nano /home/pi/scripts/AI4Glaciers.sh
```

### 3. Run WittyPi software
```bash
sudo sh wittipi/WittyPi.sh
```
- [ ] Syncronize time (Internet enabled)
- [ ] Load AI4G schedule




