#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=77
export TURTLEBOT3_MODEL=burger
RATE="${RATE:-1.0}"
EVERY="${EVERY:-30}"
if [ $# -eq 0 ]; then
    echo "Uso: ./slam_bag.bash bag1 [bag2 bag3 ...]"
    echo "Con varios bags los une en orden y hace un solo mapa"
    exit 1
fi
for B in "$@"; do
    if [ ! -f "${B%/}/metadata.yaml" ]; then
        echo "No es un bag: $B"
        exit 1
    fi
done
NAME="$(basename "${1%/}")"
[ $# -gt 1 ] && NAME="${NAME}_y_$(($# - 1))_mas"
CLEAN="${NAME}_sensores"
OUT="mapas_${NAME}"
rm -rf "$CLEAN"
mkdir -p "$OUT"
python3 - "$CLEAN" "$@" <<'PY'
import sys
import rosbag2_py
from rclpy.serialization import deserialize_message, serialize_message
from tf2_msgs.msg import TFMessage
dst, srcs = sys.argv[1], [s.rstrip('/') for s in sys.argv[2:]]
keep = {'/scan', '/odom', '/tf', '/tf_static', '/robot_description'}
w = rosbag2_py.SequentialWriter()
w.open(rosbag2_py.StorageOptions(uri=dst, storage_id='sqlite3'), rosbag2_py.ConverterOptions('cdr', 'cdr'))
readers = []
created = set()
for src in srcs:
    r = rosbag2_py.SequentialReader()
    r.open(rosbag2_py.StorageOptions(uri=src, storage_id='sqlite3'), rosbag2_py.ConverterOptions('cdr', 'cdr'))
    for t in r.get_all_topics_and_types():
        if t.name in keep and t.name not in created:
            w.create_topic(t)
            created.add(t.name)
    first = None
    while r.has_next():
        first = r.read_next()
        break
    readers.append((first[2] if first else 0, src, r, first))
readers.sort(key=lambda x: x[0])
def messages():
    for _, src, r, first in readers:
        if first:
            yield first
        while r.has_next():
            yield r.read_next()
n = removed = 0
static_done = False
for topic, data, stamp in messages():
    if topic == '/tf_static':
        if static_done:
            continue
        static_done = True
    if topic not in keep:
        continue
    if topic == '/tf':
        m = deserialize_message(data, TFMessage)
        tr = [x for x in m.transforms if x.header.frame_id != 'map']
        if len(tr) != len(m.transforms):
            removed += 1
            if not tr:
                continue
            m.transforms = tr
            data = serialize_message(m)
    w.write(topic, data, stamp)
    n += 1
del w
print('Bag preparado: %d mensajes de sensores, %d TF map->odom antiguos quitados' % (n, removed))
PY
[ -f "$CLEAN/metadata.yaml" ] || exit 1
ros2 launch turtlebot3_cartographer cartographer.launch.py use_sim_time:=True > "$OUT/cartographer.log" 2>&1 &
SLAM=$!
sleep 8
ros2 bag play "$CLEAN" --clock --rate "$RATE" > /dev/null 2>&1 &
PLAY=$!
N=0
save() {
    F="$OUT/map_$(printf %02d $N)"
    if ros2 run nav2_map_server map_saver_cli -f "$F" --ros-args -p use_sim_time:=true > /dev/null 2>&1; then
        echo "Guardado $F"
        N=$((N + 1))
    fi
}
sleep 10
while kill -0 $PLAY 2> /dev/null; do
    save
    sleep "$EVERY"
done
sleep 3
save
kill -TERM $SLAM 2> /dev/null
pkill -TERM -f "[c]artographer_node|[c]artographer_occupancy_grid_node|[r]viz2 -d .*tb3_cartographer"
wait $SLAM 2> /dev/null
sleep 2
rm -rf "$CLEAN"
echo "Mapas en $OUT"
