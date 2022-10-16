
cp ./ /opt/kasse
cp nfckasse.service /etc/systemd/system/
systremctl enable nfckasse.service
cd /opt/kasse
pip3 install -r requirements.txt

systremctl start nfckasse.service

#optional
sudo iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 80 -j REDIRECT --to-port 5000
