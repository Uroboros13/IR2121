#!/bin/bash
if [ -z "$1" ]; then
    echo "Uso: $0 <directorio_del_bag>"
    exit 1
fi
BAG="$(readlink -f "$1")"
if [ ! -f "$BAG/metadata.yaml" ]; then
    echo "$1 no es un bag válido: falta metadata.yaml"
    exit 1
fi
source /opt/ros/humble/setup.bash
ros2 bag info "$BAG"
python3 - "$BAG" <<'EOF'
import sys, math
import rosbag2_py
from rclpy.serialization import deserialize_message
from nav_msgs.msg import Odometry
r = rosbag2_py.SequentialReader()
r.open(rosbag2_py.StorageOptions(uri=sys.argv[1], storage_id='sqlite3'), rosbag2_py.ConverterOptions('cdr', 'cdr'))
r.set_filter(rosbag2_py.StorageFilter(topics=['/odom']))
xs, ys = [], []
while r.has_next():
    _, data, _ = r.read_next()
    p = deserialize_message(data, Odometry).pose.pose.position
    xs.append(p.x)
    ys.append(p.y)
if not xs:
    print('/odom: SIN MENSAJES')
    sys.exit(1)
d = sum(math.hypot(xs[i + 1] - xs[i], ys[i + 1] - ys[i]) for i in range(len(xs) - 1))
print('/odom: %d mensajes, x de %.2f a %.2f m, y de %.2f a %.2f m, recorrido %.2f m' % (len(xs), min(xs), max(xs), min(ys), max(ys), d))
print('MOVIMIENTO OK' if d > 1.0 else 'EL ROBOT APENAS SE HA MOVIDO')
EOF
