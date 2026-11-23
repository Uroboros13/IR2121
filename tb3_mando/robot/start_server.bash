#!/bin/bash
DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
source /opt/ros/humble/setup.bash
cd "$DIR"
exec python3 "$DIR/tb3_phone_server.py"
