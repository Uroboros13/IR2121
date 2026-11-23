#!/bin/bash
source /opt/ros/humble/setup.bash
rviz2 -d nav2_view.rviz --ros-args -p use_sim_time:=true
