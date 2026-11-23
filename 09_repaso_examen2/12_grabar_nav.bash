#!/bin/bash
source /opt/ros/humble/setup.bash
rm -rf rosbag_nav
ros2 bag record -o rosbag_nav /clock /odom /scan /tf /tf_static /robot_description /map /initialpose /amcl_pose /particle_cloud /goal_pose /plan /local_plan /cmd_vel /global_costmap/costmap /local_costmap/costmap
