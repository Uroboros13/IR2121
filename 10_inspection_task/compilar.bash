#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=waffle_pi
cd "$(dirname "$(readlink -f "$0")")"
colcon build
echo "Listo. Ahora ./ejecutar.bash"
