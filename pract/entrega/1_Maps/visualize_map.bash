#!/bin/bash
cd "$(dirname "$(readlink -f "$0")")"
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
rviz2 -d config_map.rviz
