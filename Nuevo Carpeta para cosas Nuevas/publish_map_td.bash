#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ros2 run nav2_map_server map_server --ros-args \
    -p yaml_filename:="${SCRIPT_DIR}/Worlds/TD_n1.yaml" \
    -p use_sim_time:=true &
MAP_PID=$!
trap "kill $MAP_PID 2>/dev/null" EXIT
sleep 3
ros2 run nav2_util lifecycle_bringup map_server
wait $MAP_PID
