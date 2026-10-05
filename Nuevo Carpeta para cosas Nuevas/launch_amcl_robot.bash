#!/bin/bash
source /opt/ros/humble/setup.bash

export ROS_DOMAIN_ID=30  # Reemplaza con tu DOMAIN ID
export TURTLEBOT3_MODEL=burger

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCH_FILE="${SCRIPT_DIR}/Worlds/scripts/amcl.launch.py"
MAP_FILE="${SCRIPT_DIR}/Worlds/TD_n1.yaml"

ros2 launch "${LAUNCH_FILE}" use_sim_time:=False map:="${MAP_FILE}"
