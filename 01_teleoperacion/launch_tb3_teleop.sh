#!/bin/bash
# Por si acaso, esto hará que funcione tanto en Jazzy (24.04) como en Humble (22.04), espero
if [ -d "/opt/ros/jazzy" ]; then
    source /opt/ros/jazzy/setup.bash

elif [ -d "/opt/ros/humble" ]; then
    source /opt/ros/humble/setup.bash
else
    echo "ERROR, Ros2 no encontrado, ¿puede que no esté instalado?"
    exit 1
fi
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
ros2 run turtlebot3_teleop teleop_keyboard
