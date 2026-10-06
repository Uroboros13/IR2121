#!/bin/bash
if [ -z "$1" ]; then
    echo "Uso: $0 <ROS_DOMAIN_ID del robot>"
    exit 1
fi
source /opt/ros/humble/setup.bash
unset ROS_LOCALHOST_ONLY
export ROS_DOMAIN_ID=$1
export TURTLEBOT3_MODEL=${TURTLEBOT3_MODEL:-burger}
ros2 run turtlebot3_teleop teleop_keyboard
