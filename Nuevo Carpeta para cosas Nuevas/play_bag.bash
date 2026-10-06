#!/bin/bash
if [ -z "$1" ]; then
    echo "Se espera un directorio: $0 <directorio_del_bag>"
    exit 1
fi
if [ ! -d "$1" ]; then
    echo "$1 no es un directorio"
    exit 1
fi
if [ ! -f "$1/metadata.yaml" ]; then
    echo "$1 no es un bag válido: falta metadata.yaml"
    exit 1
fi
source /opt/ros/humble/setup.bash
ros2 bag play "$1"
