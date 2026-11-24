#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=waffle_pi
cd "$(dirname "$(readlink -f "$0")")"
if [ "$1" = "sin_gui" ]; then
  ros2 launch ./turtlebot3_no_GUI.launch.py
else
  ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
fi
