#!/bin/bash
source /opt/ros/humble/setup.bash

export TURTLEBOT3_MODEL=burger

# Descomenta según el entorno en el que estés trabajando:
# export ROS_LOCALHOST_ONLY=1  # Para Simulación
export ROS_DOMAIN_ID=30    # Para Robot Físico

ros2 run turtlebot3_teleop teleop_keyboard
