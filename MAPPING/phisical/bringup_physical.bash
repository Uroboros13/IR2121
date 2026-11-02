#!/bin/bash

# Ejecuta los comandos DENTRO del robot vía SSH
ssh ubuntu@192.168.0.107 "source /opt/ros/humble/setup.bash && export TURTLEBOT3_MODEL=burger && export LDS_MODEL=LDS-01 && export ROS_DOMAIN_ID=7 && ros2 launch turtlebot3_bringup robot.launch.py"
