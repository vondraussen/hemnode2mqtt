#!/bin/bash
pip3 install -r requirements.txt
sudo mkdir -p /usr/local/lib/hemnode2mqtt
sudo cp hemnode2mqtt.py /usr/local/lib/hemnode2mqtt/hemnode2mqtt.py
sudo chown ${USER}:${USER} /usr/local/lib/hemnode2mqtt/hemnode2mqtt.py
sed "s/##USER##/${USER}/" hemnode2mqtt.service > hemnode2mqtt_.service
sudo cp hemnode2mqtt_.service /etc/systemd/system/hemnode2mqtt.service
rm hemnode2mqtt_.service
sudo systemctl daemon-reload
sudo systemctl enable hemnode2mqtt
sudo systemctl start hemnode2mqtt
