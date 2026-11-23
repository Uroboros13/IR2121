#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=10
rviz2 -d config_robot_physical.rviz
