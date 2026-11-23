#!/bin/bash
cd "$(dirname "$(readlink -f "$0")")"
IP="${1:-169.254.92.124}"
DOMAIN="${2:-10}"
LDS="${3:-LDS-01}"
PIN="${4:-131576}"
echo "Buscando el robot en $IP..."
for i in $(seq 10); do
    ping -c 1 -W 2 "$IP" > /dev/null && break
    sleep 1
done
if ! ping -c 1 -W 2 "$IP" > /dev/null; then
    echo "No llego al robot en $IP. Conecta el cable y ejecuta: nmcli con up robot-cable"
    exit 1
fi
SOCK="/tmp/tb3_ssh_$$"
OPTS=(-o ControlMaster=auto -o ControlPath="$SOCK" -o ControlPersist=120 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR)
echo "Contraseña del robot: turtlebot"
ssh "${OPTS[@]}" ubuntu@"$IP" 'mkdir -p ~/tb3_phone' || exit 1
scp "${OPTS[@]}" -q robot/tb3_phone_server.py robot/start_server.bash robot/start_temporal.bash robot/usb_watch.bash robot/50-usb-tether.network robot/uninstall_robot.bash ubuntu@"$IP":~/tb3_phone/ || exit 1
echo "Archivos copiados. Ahora pide la contraseña de sudo (turtlebot):"
ssh "${OPTS[@]}" -t ubuntu@"$IP" "bash ~/tb3_phone/start_temporal.bash $DOMAIN $LDS $PIN"
if ssh "${OPTS[@]}" ubuntu@"$IP" "pgrep -f tb3_phone_server.py > /dev/null"; then
    echo "LISTO. Enchufa el móvil, activa «Compartir conexión por USB» y en la app pulsa «Buscar robot». PIN: $PIN"
else
    echo "El servidor no ha arrancado. Pásale esto a Claude:"
    ssh "${OPTS[@]}" ubuntu@"$IP" "sed -n '/=== arranque/,\$p' ~/tb3_phone/server.log | tail -n 40"
fi
ssh "${OPTS[@]}" -O exit ubuntu@"$IP" 2> /dev/null
