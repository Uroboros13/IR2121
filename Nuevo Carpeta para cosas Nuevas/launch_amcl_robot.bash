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
ros2 launch "${SCRIPT_DIR}/Worlds/scripts/amcl.launch.py" \
    use_sim_time:=False \
    map:="${SCRIPT_DIR}/Worlds/TD_n1.yaml"
