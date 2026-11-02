#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=7
export LDS_MODEL=LDS-01
export TURTLEBOT3_MODEL=burger

ros2 bag record /map /map_updates /odom /robot_description /scan /scan_matched_points2 /submap_list /tf /tf_static 
