#!/bin/bash
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=waffle_pi
MAP="${1:-maps/map_rtabmap_5.yaml}"
SHARE=$(ros2 pkg prefix turtlebot3_navigation2)/share/turtlebot3_navigation2/param
PARAMS="$SHARE/humble/waffle_pi.yaml"
[ -f "$PARAMS" ] || PARAMS="$SHARE/waffle_pi.yaml"
ros2 launch nav2_bringup bringup_launch.py use_sim_time:=True map:="$PWD/$MAP" params_file:="$PARAMS"
