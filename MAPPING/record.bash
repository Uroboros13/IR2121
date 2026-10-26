#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger

ros2 bag record /clock /map /map_updates /odom /robot_description /scan /scan_matched_points2 /submap_list /tf /tf_static
