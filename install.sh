#!/bin/bash

ERR=0
if ! grep -q "^dtparam=i2c_arm=on" /boot/firmware/config.txt
then
	echo "Enable I2C in raspi-config!"
	ERR=1
fi
if ! grep -q "^dtparam=spi=on" /boot/firmware/config.txt
then
	echo "Enable SPI in raspi-config!"
	ERR=1
fi
if ! grep -q "^dtoverlay=spi0-0cs" /boot/firmware/config.txt
then
	echo "Add dtoverlay=spi0-0cs to /boot/firmware/config.txt!"
	ERR=1
fi
if [ !-f settings.py ]
then
	echo "Please make sure to setup settings.py before running this script."
	ERR=1
fi
if [ $ERR -eq 1 ]
then
	echo "Quitting this script now, please fix the errors above first."
	exit 1
fi
echo "Make sure to disable console via Serial (while keeping Serial enabled). Use raspi-config."

cp -r ./ /opt/kasse
cp nfckasse.service /etc/systemd/system/
systemctl enable nfckasse.service
cd /opt/kasse

sudo apt update
# Install required packages
sudo apt install libfreetype6-dev libjpeg-dev libffi-dev python3-setuptools swig python3-dev python3-venv fonts-dejavu
# Manually build lg for lgpio
wget http://abyz.me.uk/lg/lg.zip
unzip lg.zip
cd lg
make
sudo make install
cd ..
# Cleanup
rm -r lg.zip lg
# Create venv
python -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

# You probably should reboot, trying to start service anyway
systemctl start nfckasse.service
