#!/bin/bash
source /opt/ros/humble/setup.bash

export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger

MAP_PATH="../TD_n1.yaml"

ros2 launch amcl.launch.py use_sim_time:=True map:=${MAP_PATH}
