#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=30
export TURTLEBOT3_MODEL=burger
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ros2 launch "${SCRIPT_DIR}/Worlds/scripts/amcl.launch.py" \
    use_sim_time:=False \
    map:="${SCRIPT_DIR}/Worlds/TD_n1.yaml"
