#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=10
ros2 bag record /map /odom /scan /tf /tf_static
