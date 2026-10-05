#!/bin/bash

source /opt/ros/humble/setup.bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 <bag_directory>"
    exit 1
fi

ros2 bag play "$1"
