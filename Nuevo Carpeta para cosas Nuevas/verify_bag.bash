#!/bin/bash
source /opt/ros/humble/setup.bash

export ROS_LOCALHOST_ONLY=1

if [ -z "$1" ]; then
  echo "Uso: ./verify_bag.bash <nombre_o_ruta_de_carpeta_bag>"
  exit 1
fi

echo "Reproduciendo bag: $1"
ros2 bag play "$1"
