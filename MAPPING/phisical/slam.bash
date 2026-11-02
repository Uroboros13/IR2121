#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=7
export TURTLEBOT3_MODEL=burger
export LDS_MODEL=LDS-01
ros2 launch turtlebot3_cartographer cartographer.launch.py use_sim_time:=False
