#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=30
ros2 bag record \
    /map \
    /odom \
    /scan \
    /tf \
    /tf_static \
    /amcl_pose \
    /particle_cloud \
    /robot_description
