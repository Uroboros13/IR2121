#!/bin/bash
source /opt/ros/humble/setup.bash
rviz2 -d config_teleop.rviz --ros-args -p use_sim_time:=true
