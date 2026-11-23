#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=10
ros2 run tf2_ros static_transform_publisher --x -5.5 --y 20 --z 0 \
  --qx 0 --qy 0 --qz 0.12 --qw 1 --frame-id map --child-frame-id odom
