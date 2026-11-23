#!/bin/bash
pkill -f tb3_phone_server.py
sudo pkill -f usb_watch.bash
crontab -l 2>/dev/null | grep -v "tb3_phone\|start_server.bash" | crontab -
if [ -f /etc/systemd/network/50-usb-tether.network ]; then
    sudo rm /etc/systemd/network/50-usb-tether.network
    sudo networkctl reload
fi
sudo rm -f /run/systemd/network/50-usb-tether.network
echo "Mando movil desinstalado del arranque. La carpeta ~/tb3_phone se puede borrar a mano."
