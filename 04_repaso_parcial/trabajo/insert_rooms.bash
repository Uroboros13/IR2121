#!/bin/bash
cd "$(dirname "$(readlink -f "$0")")"
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 run gazebo_ros spawn_entity.py -entity rooms -file models/rooms/model.sdf -x 0 -y 0 -z 0
