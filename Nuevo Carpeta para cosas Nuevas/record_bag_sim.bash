#!/bin/bash
source /opt/ros/humble/setup.bash

export ROS_LOCALHOST_ONLY=1
BAG_NAME="sim_localization_bag_$(date +%Y%m%d_%H%M%S)"

echo "Grabando datos de simulación en: ${BAG_NAME}..."
ros2 bag record -o ${BAG_NAME} \
    /clock \
    /map \
    /odom \
    /scan \
    /tf \
    /tf_static \
    /amcl_pose \
    /particle_cloud \
    /robot_description
