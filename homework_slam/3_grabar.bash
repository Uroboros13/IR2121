#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
NAME="rosbag_td_$(date +%Y_%m_%d-%H_%M_%S)"
ros2 bag record -o "$NAME" /clock /odom /robot_description /scan /tf /tf_static
