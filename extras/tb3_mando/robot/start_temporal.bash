#!/bin/bash
DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
DOMAIN="${1:-10}"
LDS="${2:-LDS-01}"
PIN="${3:-}"
python3 - "$DIR/config.json" "$DOMAIN" "$LDS" "$PIN" <<'PY'
import json, os, secrets, sys
path, domain, lds, pin = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
cfg = json.load(open(path)) if os.path.exists(path) else {}
cfg['domain_id'] = domain
cfg['lds_model'] = lds
cfg.setdefault('port', 8080)
if pin:
    cfg['token'] = pin
cfg.setdefault('token', '%06d' % secrets.randbelow(1000000))
json.dump(cfg, open(path, 'w'), indent=2)
print('PIN para la app:', cfg['token'])
print('ROS_DOMAIN_ID:', domain, ' LDS_MODEL:', lds)
PY
sudo -v || exit 1
sudo mkdir -p /run/systemd/network
sudo cp "$DIR/50-usb-tether.network" /run/systemd/network/50-usb-tether.network
sudo networkctl reload 2> /dev/null
sudo pkill -f usb_watch.bash
sudo nohup bash "$DIR/usb_watch.bash" > /dev/null 2>&1 &
pkill -f tb3_phone_server.py
for i in $(seq 10); do
    pgrep -f tb3_phone_server.py > /dev/null || break
    sleep 1
done
pkill -9 -f tb3_phone_server.py
echo "=== arranque $(date '+%F %T') ===" >> "$DIR/server.log"
setsid nohup bash "$DIR/start_server.bash" >> "$DIR/server.log" 2>&1 < /dev/null &
echo "Arrancando el servidor (tarda unos segundos)..."
for i in $(seq 40); do
    if python3 -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8080/api/ping',timeout=2)" 2> /dev/null; then
        echo "Servidor en marcha en el puerto 8080"
        break
    fi
    pgrep -f tb3_phone_server.py > /dev/null || break
    sleep 1
done
echo "Modo temporal: al apagar o reiniciar el robot no queda nada activo."
