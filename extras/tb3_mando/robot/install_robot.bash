#!/bin/bash
DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
DOMAIN="${1:-10}"
LDS="${2:-LDS-01}"
chmod +x "$DIR/start_server.bash" "$DIR/tb3_phone_server.py"
python3 - "$DIR/config.json" "$DOMAIN" "$LDS" <<'PY'
import json, os, secrets, sys
path, domain, lds = sys.argv[1], int(sys.argv[2]), sys.argv[3]
cfg = json.load(open(path)) if os.path.exists(path) else {}
cfg['domain_id'] = domain
cfg['lds_model'] = lds
cfg.setdefault('port', 8080)
cfg.setdefault('token', '%06d' % secrets.randbelow(1000000))
json.dump(cfg, open(path, 'w'), indent=2)
print('PIN para la app:', cfg['token'])
print('ROS_DOMAIN_ID:', domain, ' LDS_MODEL:', lds)
PY
LINE="@reboot sleep 20 && $DIR/start_server.bash >> $DIR/server.log 2>&1"
( crontab -l 2>/dev/null | grep -v "tb3_phone\|start_server.bash" ; echo "$LINE" ) | crontab -
echo "Arranque automatico al encender el robot: activado"
if [ "$3" == "--usb" ]; then
    sudo cp "$DIR/50-usb-tether.network" /etc/systemd/network/50-usb-tether.network
    sudo networkctl reload
    echo "Red por USB del movil: configurada"
fi
pkill -f tb3_phone_server.py
sleep 1
nohup "$DIR/start_server.bash" >> "$DIR/server.log" 2>&1 &
sleep 4
tail -n 3 "$DIR/server.log"
