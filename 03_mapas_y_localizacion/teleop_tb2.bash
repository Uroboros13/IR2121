#!/bin/bash

# ROS_DOMAIN_ID por defecto = 25 (si no se pasa argumento)
DOMAIN_ID=${1:-25}
# Tópico por defecto = /cmd_vel
TOPIC_VEL=${2:-/cmd_vel}

source /opt/ros/humble/setup.bash

if [ -f ~/kobuki_ws/install/setup.bash ]; then
    source ~/kobuki_ws/install/setup.bash
fi

unset ROS_LOCALHOST_ONLY
export ROS_DOMAIN_ID=$DOMAIN_ID

echo "Lanzando teleoperación en ROS_DOMAIN_ID=$ROS_DOMAIN_ID sobre el tópico $TOPIC_VEL..."

ros2 run teleop_twist_keyboard teleop_twist_keyboard \
    --ros-args -r cmd_vel:=$TOPIC_VEL
