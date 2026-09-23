#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 bag record /clock /map /odom /scan /tf /tf_static
