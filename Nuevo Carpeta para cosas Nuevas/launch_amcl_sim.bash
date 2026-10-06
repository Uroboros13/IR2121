#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ros2 launch "${SCRIPT_DIR}/Worlds/scripts/amcl.launch.py" \
    use_sim_time:=True \
    map:="${SCRIPT_DIR}/Worlds/TD_n1.yaml"
