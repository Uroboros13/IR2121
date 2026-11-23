#!/bin/bash
cd "$(dirname "$(readlink -f "$0")")"
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 bag record -o "rosbag_teleop_$(date +%Y_%m_%d-%H_%M_%S)" /map /clock /tf /tf_static /robot_description /odom /scan
