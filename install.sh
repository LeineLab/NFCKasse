
cp ./ /opt/kasse
cp nfckasse.service /etc/systemd/system/
systremctl enable nfckasse.service
cd /opt/kasse
pip3 install -r requirements.txt

systremctl start nfckasse.service
