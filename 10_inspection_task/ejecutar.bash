#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=waffle_pi
cd "$(dirname "$(readlink -f "$0")")"
USE_SIM_TIME=${USE_SIM_TIME:-true}
source install/setup.bash
f(){ case "$1" in *.*) echo "$1";; *) echo "$1.0";; esac; }
X=$(f "${1:-0.55}")
Y=$(f "${2:-0.55}")
YAW=$(f "${3:-0.0}")
ros2 run inspection_task go_to_goal --ros-args -p use_sim_time:=$USE_SIM_TIME -p x:=$X -p y:=$Y -p yaw:=$YAW
