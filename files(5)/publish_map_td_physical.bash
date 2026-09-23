#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=10
ros2 launch map_server_td_physical.launch.py
