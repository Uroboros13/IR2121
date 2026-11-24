#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=waffle_pi
cd "$(dirname "$(readlink -f "$0")")"
ros2 run rqt_image_view rqt_image_view /camera/image_raw
