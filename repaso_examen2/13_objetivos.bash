#!/bin/bash
source /opt/ros/humble/setup.bash
goal() {
    echo "Objetivo $1: x=$2 y=$3"
    ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: map}, pose: {position: {x: $2, y: $3, z: 0.0}, orientation: {z: $4, w: $5}}}}"
}
goal 1 -0.55 -0.55 0.0 1.0
goal 2 0.55 0.55 0.707 0.707
goal 3 1.60 -0.50 0.0 1.0
goal 4 0.55 -0.55 1.0 0.0
goal 5 -2.00 -0.50 1.0 0.0
