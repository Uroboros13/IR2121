#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
ALG="$1"
BAG="${2%/}"
RATE="${3:-1.0}"
EVERY="${4:-20}"
if [ ! -f "$BAG/metadata.yaml" ] || [[ ! "$ALG" =~ ^(cartographer|toolbox|rtabmap)$ ]]; then
    echo "Uso: ./4_slam.bash cartographer|toolbox|rtabmap carpeta_del_bag [velocidad] [segundos_entre_mapas]"
    exit 1
fi
if pgrep -f gzserver > /dev/null; then
    echo "Cierra Gazebo antes: publicaría /clock y /tf a la vez que el bag"
    exit 1
fi
OUT="$PWD/mapas_${ALG}"
rm -rf "$OUT"
mkdir -p "$OUT"
case "$ALG" in
    cartographer)
        ros2 launch turtlebot3_cartographer cartographer.launch.py use_sim_time:=True > "$OUT/slam.log" 2>&1 &
        ;;
    toolbox)
        ros2 launch slam_toolbox online_async_launch.py use_sim_time:=True > "$OUT/slam.log" 2>&1 &
        ;;
    rtabmap)
        cat > "$OUT/rtabmap.yaml" <<YAML
rtabmap:
  ros__parameters:
    use_sim_time: true
    frame_id: base_footprint
    odom_frame_id: odom
    map_frame_id: map
    subscribe_depth: false
    subscribe_rgb: false
    subscribe_rgbd: false
    subscribe_scan: true
    approx_sync: true
    database_path: "$OUT/rtabmap.db"
    Reg/Strategy: "1"
    Reg/Force3DoF: "true"
    RGBD/NeighborLinkRefining: "true"
    RGBD/ProximityBySpace: "true"
    RGBD/AngularUpdate: "0.05"
    RGBD/LinearUpdate: "0.05"
    Grid/Sensor: "0"
    Grid/FromDepth: "false"
    Grid/RangeMax: "3.5"
    Grid/CellSize: "0.05"
    Icp/VoxelSize: "0.05"
    Icp/MaxCorrespondenceDistance: "0.1"
    Optimizer/GravitySigma: "0"
YAML
        ros2 topic echo /map nav_msgs/msg/OccupancyGrid --qos-durability transient_local --qos-reliability reliable --no-arr > /dev/null 2>&1 &
        ros2 run rtabmap_slam rtabmap --delete_db_on_start --ros-args --params-file "$OUT/rtabmap.yaml" -r scan:=/scan > "$OUT/slam.log" 2>&1 &
        ;;
esac
SLAM=$!
sleep 8
ros2 bag play "$BAG" --rate "$RATE" > "$OUT/play.log" 2>&1 &
PLAY=$!
N=0
save() {
    F="$OUT/map_$(printf %02d $N)"
    if timeout 20 ros2 run nav2_map_server map_saver_cli -f "$F" -t /map --ros-args -p use_sim_time:=true -p save_map_timeout:=10.0 > /dev/null 2>&1 \
        || timeout 20 ros2 run nav2_map_server map_saver_cli -f "$F" -t /map --ros-args -p use_sim_time:=true -p save_map_timeout:=10.0 -p map_subscribe_transient_local:=false > /dev/null 2>&1; then
        echo "$ALG: guardado map_$(printf %02d $N)"
        N=$((N + 1))
    else
        echo "$ALG: todavía no hay /map"
    fi
}
sleep 5
while kill -0 $PLAY 2> /dev/null; do
    save
    sleep "$EVERY"
done
sleep 5
save
NODES="rviz2 cartographer_node cartographer_occupancy_grid_node async_slam_toolbox_node rtabmap_slam/rtabmap nav_msgs/msg/OccupancyGrid"
kill -TERM $SLAM 2> /dev/null
for P in $NODES; do pkill -TERM -f "$P" 2> /dev/null; done
sleep 3
for P in $NODES; do pkill -9 -f "$P" 2> /dev/null; done
timeout 10 tail --pid=$SLAM -f /dev/null
echo "$ALG terminado: $N mapas en mapas_${ALG}"
