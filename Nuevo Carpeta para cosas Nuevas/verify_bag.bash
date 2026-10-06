#!/bin/bash
if [ -z "$1" ]; then
    echo "Se espera un directorio: $0 <directorio_del_bag>"
    exit 1
fi
source /opt/ros/humble/setup.bash
ros2 bag info "$1"
