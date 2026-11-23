#!/bin/bash
if [ -z "$1" ]; then
    echo "Uso: $0 <directorio_del_bag>"
    exit 1
fi
BAG="$(readlink -f "$1")"
if [ ! -f "$BAG/metadata.yaml" ]; then
    echo "$1 no es un bag válido: falta metadata.yaml"
    exit 1
fi
cd "$(dirname "$(readlink -f "$0")")"
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 bag info "$BAG"
ros2 bag play "$BAG"
