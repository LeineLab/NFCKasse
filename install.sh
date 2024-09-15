#!/bin/bash
if [ !-f settings.py ]
then
	echo "Please make sure to setup the database and settings.py before running this script."
	exit 1
fi
cp -r ./ /opt/kasse
cp nfckasse.service /etc/systemd/system/
systemctl enable nfckasse.service
cd /opt/kasse
python -m venv venv
venv/bin/pip install -r requirements.txt

systemctl start nfckasse.service

#optional
sudo iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 80 -j REDIRECT --to-port 5000
