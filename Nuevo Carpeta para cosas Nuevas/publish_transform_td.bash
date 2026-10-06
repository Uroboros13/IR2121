#!/bin/bash
if [ $# -lt 2 ]; then
    echo "Uso: $0 <x> <y> [yaw en radianes]"
    exit 1
fi
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 run tf2_ros static_transform_publisher \
    --x "$1" --y "$2" --z 0 --yaw "${3:-0}" \
    --frame-id map --child-frame-id odom
