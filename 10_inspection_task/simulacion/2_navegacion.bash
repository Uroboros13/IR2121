#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=waffle_pi
cd "$(dirname "$(readlink -f "$0")")"
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True map:=$PWD/maps/turtlebot3_world.yaml
