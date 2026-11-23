#!/bin/bash
source /opt/ros/humble/setup.bash
unset ROS_LOCALHOST_ONLY
export ROS_DOMAIN_ID=10
python3 - <<'PY'
import math, time, rclpy
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan
rclpy.init()
node = rclpy.create_node('check_scan')
stamps, valid = [], []
def cb(msg):
    stamps.append(time.time())
    valid.append(sum(1 for r in msg.ranges if math.isfinite(r) and msg.range_min < r < msg.range_max))
node.create_subscription(LaserScan, '/scan', cb, qos_profile_sensor_data)
end = time.time() + 6.0
while time.time() < end:
    rclpy.spin_once(node, timeout_sec=0.1)
if len(stamps) < 2:
    print('NO llegan mensajes de /scan: revisa bringup, ROS_DOMAIN_ID y la red')
else:
    hz = (len(stamps) - 1) / (stamps[-1] - stamps[0])
    media = sum(valid) / len(valid)
    print(f'/scan: {hz:.1f} Hz, {media:.0f} de 360 medidas validas de media')
    if hz < 4:
        print('MAL: menos de 4 Hz, conexion lenta o cortes')
    if media < 150:
        print('MAL: casi todo ceros; prueba el bringup con el otro LDS_MODEL (LDS-01 <-> LDS-02)')
    if hz >= 4 and media >= 150:
        print('OK: puedes empezar a grabar')
node.destroy_node()
rclpy.shutdown()
PY
