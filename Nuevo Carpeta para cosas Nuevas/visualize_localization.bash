#!/bin/bash

source /opt/ros/humble/setup.bash

export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

rviz2 -d "$SCRIPT_DIR/Worlds/scripts/config_amcl.rviz"
