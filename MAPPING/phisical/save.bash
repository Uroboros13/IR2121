#!/bin/bash
source /opt/ros/humble/setup.bash
unset ROS_LOCALHOST_ONLY
export ROS_DOMAIN_ID=10
COUNTER_FILE=".map_counter"
if [ "$1" == "new_save" ]; then
    echo "0" > "$COUNTER_FILE"
    echo "Contador de mapas reiniciado"
fi
if [ -f "$COUNTER_FILE" ]; then
    COUNTER=$(cat "$COUNTER_FILE")
else
    COUNTER=0
fi
MAP_NAME=$(printf "map_%02d" "$COUNTER")
echo "Guardando ./$MAP_NAME (.pgm y .yaml)"
ros2 run nav2_map_server map_saver_cli -f "./$MAP_NAME" && echo $((COUNTER + 1)) > "$COUNTER_FILE"
