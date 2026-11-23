#!/bin/bash
DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
rm -f "$DIR/.apagar"
while true; do
    if [ -f "$DIR/.apagar" ]; then
        rm -f "$DIR/.apagar"
        sync
        poweroff
        exit 0
    fi
    if ip link show usb0 > /dev/null 2>&1 && ! ip -4 addr show usb0 | grep -q inet; then
        ip link set usb0 up
        timeout 25 dhclient -1 usb0
    fi
    sleep 2
done
