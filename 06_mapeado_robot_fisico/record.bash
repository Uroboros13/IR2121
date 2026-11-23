#!/bin/bash
source /opt/ros/humble/setup.bash
unset ROS_LOCALHOST_ONLY
export ROS_DOMAIN_ID=10
export TURTLEBOT3_MODEL=burger
ros2 bag record -o "rosbag_mapping_$(date +%Y_%m_%d-%H_%M_%S)" /map /map_updates /odom /robot_description /scan /scan_matched_points2 /submap_list /tf /tf_static
