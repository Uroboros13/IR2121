#!/bin/bash
if [ -z "$1" ]; then
    echo "Uso: $0 <ROS_DOMAIN_ID del robot>"
    exit 1
fi
source /opt/ros/humble/setup.bash
unset ROS_LOCALHOST_ONLY
export ROS_DOMAIN_ID=$1
echo "== Topics visibles (dominio $1)"
ros2 topic list --no-daemon
echo "== /odom"
timeout 10 ros2 topic echo --once --no-arr /odom || echo "No llega /odom"
echo "== Frecuencia de /scan"
timeout 8 ros2 topic hz /scan --qos-reliability best_effort || true
