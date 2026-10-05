#!/bin/bash
source /opt/ros/humble/setup.bash

export ROS_DOMAIN_ID=30  # REEMPLAZAR CON TU ID
export TURTLEBOT3_MODEL=burger

MAP_PATH="../TD_n1.yaml"

ros2 launch amcl.launch.py use_sim_time:=False map:=${MAP_PATH}
