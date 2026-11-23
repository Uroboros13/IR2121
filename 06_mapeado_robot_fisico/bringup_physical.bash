#!/bin/bash
if [ -z "$1" ]; then
    echo "Uso: $0 <IP_del_robot> [LDS-01|LDS-02] [ROS_DOMAIN_ID]"
    exit 1
fi
ROBOT_IP="$1"
LDS="${2:-LDS-01}"
DOMAIN="${3:-10}"
ssh -t ubuntu@"$ROBOT_IP" "source /opt/ros/humble/setup.bash && export TURTLEBOT3_MODEL=burger && export LDS_MODEL=$LDS && export ROS_DOMAIN_ID=$DOMAIN && ros2 launch turtlebot3_bringup robot.launch.py"
