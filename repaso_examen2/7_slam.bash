#!/bin/bash
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=waffle_pi
ALG="$1"
BAG="${2:-rosbag_teleop}"
RATE="${3:-1.0}"
case "$ALG" in
    toolbox) NAME=slam_toolbox ;;
    cartographer) NAME=cartographer ;;
    rtabmap) NAME=rtabmap ;;
    *) echo "Uso: ./7_slam.bash toolbox|cartographer|rtabmap [bag] [velocidad]"; exit 1 ;;
esac
if [ ! -f "$BAG/metadata.yaml" ]; then
    echo "No encuentro el bag $BAG"
    exit 1
fi
if pgrep -f gzserver > /dev/null; then
    echo "Cierra la simulación antes: publicaría /clock y /tf a la vez que el bag"
    exit 1
fi
mkdir -p maps logs
DUR=$(python3 -c "import yaml,sys;print(yaml.safe_load(open(sys.argv[1]))['rosbag2_bagfile_information']['duration']['nanoseconds']/1e9)" "$BAG/metadata.yaml")
STEP=$(python3 -c "print(max(5.0, $DUR / 5 / $RATE))")
case "$ALG" in
    toolbox)
        ros2 launch slam_toolbox online_async_launch.py use_sim_time:=True > logs/slam_$NAME.log 2>&1 &
        ;;
    cartographer)
        ros2 launch turtlebot3_cartographer cartographer.launch.py use_sim_time:=True > logs/slam_$NAME.log 2>&1 &
        ;;
    rtabmap)
        cat > logs/rtabmap.yaml <<YAML
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
    database_path: "$PWD/logs/rtabmap.db"
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
        ros2 run rtabmap_slam rtabmap --delete_db_on_start --ros-args --params-file logs/rtabmap.yaml -r scan:=/scan > logs/slam_$NAME.log 2>&1 &
        SLAM=$!
        ros2 topic hz /map > /dev/null 2>&1 &
        MAPSUB=$!
        ;;
esac
[ "$ALG" = rtabmap ] || SLAM=$!
sleep 8
ros2 bag play "$BAG" --rate "$RATE" > logs/play_$NAME.log 2>&1 &
PLAY=$!
save() {
    F="maps/map_${NAME}_$1"
    for TL in true false; do
        if timeout 25 ros2 run nav2_map_server map_saver_cli -f "$F" -t /map --ros-args -p use_sim_time:=true -p save_map_timeout:=10.0 -p map_subscribe_transient_local:=$TL > /dev/null 2>&1; then
            echo "Guardado $F"
            return
        fi
    done
    echo "No se pudo guardar $F"
}
for N in 1 2 3 4; do
    sleep "$STEP"
    save $N
done
while kill -0 $PLAY 2> /dev/null; do
    sleep 1
done
sleep 5
save 5
NODES="rviz2 cartographer_node cartographer_occupancy_grid_node async_slam_toolbox_node rtabmap_slam/rtabmap"
kill -TERM $SLAM 2> /dev/null
[ -n "$MAPSUB" ] && kill -TERM $MAPSUB 2> /dev/null
for P in $NODES; do pkill -TERM -f "$P" 2> /dev/null; done
sleep 3
for P in $NODES; do pkill -9 -f "$P" 2> /dev/null; done
timeout 10 tail --pid=$SLAM -f /dev/null
ls maps/map_${NAME}_*.pgm
