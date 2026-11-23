#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
X="${1:-0.0}"
Y="${2:-0.0}"
if [ ! -f TD_n1/model.sdf ]; then
    SRC="../Nuevo Carpeta para cosas Nuevas/Worlds/models/TD_n1"
    if [ -f "$SRC/model.sdf" ]; then
        cp -r "$SRC" .
    else
        echo "Copia en esta carpeta el modelo TD_n1 (la carpeta con model.sdf y model.config)"
        exit 1
    fi
fi
ros2 launch turtlebot3_gazebo empty_world.launch.py x_pose:="$X" y_pose:="$Y" &
SIM=$!
sleep 12
ros2 run gazebo_ros spawn_entity.py -entity TD_n1 -file "$PWD/TD_n1/model.sdf" -x 0 -y 0 -z 0
wait $SIM
