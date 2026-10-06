#!/bin/bash
if [ -z "$1" ]; then
    echo "Uso: $0 <ROS_DOMAIN_ID del robot> [topic de velocidad, por defecto /cmd_vel]"
    exit 1
fi
source /opt/ros/humble/setup.bash
unset ROS_LOCALHOST_ONLY
export ROS_DOMAIN_ID=$1
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
    --ros-args -r cmd_vel:=${2:-/cmd_vel}
