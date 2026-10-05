#!/bin/bash

source /opt/ros/humble/setup.bash

export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR/Worlds/scripts" || exit 1

ros2 launch ./amcl.launch.py \
    use_sim_time:=True \
    map:=../TD_n1.yaml
