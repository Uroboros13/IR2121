#!/bin/bash
if [ -z "$1" ]; then
    echo "Uso: $0 <ROS_DOMAIN_ID del robot>"
    exit 1
fi
source /opt/ros/humble/setup.bash
unset ROS_LOCALHOST_ONLY
export ROS_DOMAIN_ID=$1
ros2 bag record \
    /map \
    /odom \
    /scan \
    /tf \
    /tf_static \
    /amcl_pose \
    /particle_cloud \
    /robot_description
