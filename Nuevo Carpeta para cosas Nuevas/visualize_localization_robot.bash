#!/bin/bash
if [ -z "$1" ]; then
    echo "Uso: $0 <ROS_DOMAIN_ID del robot>"
    exit 1
fi
source /opt/ros/humble/setup.bash
unset ROS_LOCALHOST_ONLY
export ROS_DOMAIN_ID=$1
export TURTLEBOT3_MODEL=burger
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rviz2 -d "$SCRIPT_DIR/Worlds/scripts/config_amcl.rviz"
