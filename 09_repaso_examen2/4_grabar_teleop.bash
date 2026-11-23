#!/bin/bash
source /opt/ros/humble/setup.bash
rm -rf rosbag_teleop
ros2 bag record -o rosbag_teleop /clock /odom /scan /tf /tf_static /robot_description /imu /joint_states
