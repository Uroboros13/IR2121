#!/bin/bash
ssh ubuntu@192.168.0.110
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=burger
export LDS_MODEL=LDS-01
export ROS_DOMAIN_ID=10
ros2 launch turtlebot3_bringup robot.launch.py
