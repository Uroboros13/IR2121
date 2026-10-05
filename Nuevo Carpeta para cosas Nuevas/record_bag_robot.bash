#!/bin/bash
source /opt/ros/humble/setup.bash

export ROS_DOMAIN_ID=30  # REEMPLAZAR CON TU ID
BAG_NAME="robot_localization_bag_$(date +%Y%m%d_%H%M%S)"

echo "Grabando datos físicos en: ${BAG_NAME}..."
ros2 bag record -o ${BAG_NAME} \
    /map \
    /odom \
    /scan \
    /tf \
    /tf_static \
    /amcl_pose \
    /particle_cloud \
    /robot_description
