#!/bin/bash
cd "$(dirname "$(readlink -f "$0")")"
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
export GAZEBO_MODEL_PATH="$PWD/models:$GAZEBO_MODEL_PATH"
ros2 launch turtlebot3_gazebo empty_world.launch.py
