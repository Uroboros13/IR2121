#!/usr/bin/env python3
"""Servidor del mando movil para el TurtleBot3 (ROS 2 Humble).

Se ejecuta en el propio robot. Solo usa la biblioteca estandar de Python y
rclpy, que ya vienen con ROS 2. La app del movil habla con el por HTTP.
"""
import json
import math
import os
import secrets
import signal
import socket
import struct
import subprocess
import threading
import time
import zipfile
import zlib
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = os.path.join(HERE, 'config.json')

DEFAULT_CONFIG = {
    'port': 8080,
    'token': '',
    'domain_id': 10,
    'model': 'burger',
    'lds_model': 'LDS-01',
    'max_lin': 0.22,
    'max_ang': 2.0,
    'stamped_cmd_vel': False,
    'data_dir': os.path.join(HERE, 'datos'),
    'auto_save_seconds': 45,
    'record_topics': ['/map', '/map_updates', '/odom', '/robot_description', '/scan',
                      '/scan_matched_points2', '/submap_list', '/tf', '/tf_static'],
}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            cfg.update(json.load(f))
    if not cfg['token']:
        cfg['token'] = '%06d' % secrets.randbelow(1000000)
        with open(CONFIG_PATH, 'w') as f:
            json.dump(cfg, f, indent=2)
    cfg['data_dir'] = os.path.expanduser(cfg['data_dir'])
    os.makedirs(cfg['data_dir'], exist_ok=True)
    return cfg


CFG = load_config()
os.environ['ROS_DOMAIN_ID'] = str(CFG['domain_id'])
os.environ.pop('ROS_LOCALHOST_ONLY', None)
os.environ['TURTLEBOT3_MODEL'] = CFG['model']
os.environ['LDS_MODEL'] = CFG['lds_model']

import rclpy  # noqa: E402
from rclpy.executors import SingleThreadedExecutor  # noqa: E402
from rclpy.time import Time  # noqa: E402
from rclpy.qos import QoSProfile, DurabilityPolicy, ReliabilityPolicy, qos_profile_sensor_data  # noqa: E402
from geometry_msgs.msg import Twist  # noqa: E402
from sensor_msgs.msg import BatteryState, LaserScan  # noqa: E402
from nav_msgs.msg import OccupancyGrid, Odometry  # noqa: E402

try:
    from geometry_msgs.msg import TwistStamped  # noqa: E402
except ImportError:
    TwistStamped = None

try:
    import tf2_ros  # noqa: E402
except ImportError:
    tf2_ros = None


# ---------------------------------------------------------------- utilidades

def ros_cmd(cmd):
    return 'source /opt/ros/humble/setup.bash && exec ' + cmd


def ros_package_exists(pkg):
    try:
        r = subprocess.run(['bash', '-c', 'source /opt/ros/humble/setup.bash && ros2 pkg prefix ' + pkg],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        return r.returncode == 0
    except Exception:
        return False


TRINARY = bytes(205 if b >= 128 else (0 if b >= 65 else (254 if b <= 25 else 205)) for b in range(256))
PALETTE = b''.join(bytes((i, i, i)) for i in range(256))
PALETTE = PALETTE[:3] + b'\xdc\x14\x14' + PALETTE[6:]


def png_bytes(width, height, rows):
    raw = b''.join(b'\x00' + row for row in rows)

    def chunk(tag, data):
        c = struct.pack('>I', len(data)) + tag + data
        return c + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)

    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 3, 0, 0, 0))
            + chunk(b'PLTE', PALETTE) + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b''))


def grid_to_trinary(msg):
    w, h = msg.info.width, msg.info.height
    d = msg.data
    raw = d.tobytes() if hasattr(d, 'tobytes') else bytes(v & 0xff for v in d)
    raw = raw.translate(TRINARY)
    return w, h, [raw[y * w:(y + 1) * w] for y in range(h - 1, -1, -1)]


def write_map_files(msg, path_no_ext):
    w, h, rows = grid_to_trinary(msg)
    with open(path_no_ext + '.pgm', 'wb') as f:
        f.write(b'P5\n# CREATOR: tb3_phone_server %.3f m/pix\n%d %d\n255\n' % (msg.info.resolution, w, h))
        for r in rows:
            f.write(r)
    o = msg.info.origin
    yaw = 2.0 * math.atan2(o.orientation.z, o.orientation.w)
    with open(path_no_ext + '.yaml', 'w') as f:
        f.write('image: %s.pgm\nmode: trinary\nresolution: %.3f\norigin: [%.3f, %.3f, %.3f]\n'
                'negate: 0\noccupied_thresh: 0.65\nfree_thresh: 0.25\n'
                % (os.path.basename(path_no_ext), msg.info.resolution, o.position.x, o.position.y, yaw))


# ------------------------------------------------------------------- ROS

class RobotLink:
    def __init__(self):
        rclpy.init()
        self.node = rclpy.create_node('tb3_phone_server')
        self.lock = threading.Lock()
        if CFG.get('stamped_cmd_vel') and TwistStamped is not None:
            self.pub = self.node.create_publisher(TwistStamped, 'cmd_vel', 10)
            self.stamped = True
        else:
            self.pub = self.node.create_publisher(Twist, 'cmd_vel', 10)
            self.stamped = False
        self.target = (0.0, 0.0)
        self.target_time = 0.0
        self.zero_left = 0
        self.battery = None
        self.scan_times = []
        self.scan_valid = []
        self.odom_time = 0.0
        self.map_msg = None
        self.map_time = 0.0
        self.node.create_subscription(BatteryState, 'battery_state', self.on_battery, 10)
        self.node.create_subscription(LaserScan, 'scan', self.on_scan, qos_profile_sensor_data)
        self.node.create_subscription(Odometry, 'odom', self.on_odom, qos_profile_sensor_data)
        map_qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL,
                             reliability=ReliabilityPolicy.RELIABLE)
        self.node.create_subscription(OccupancyGrid, 'map', self.on_map, map_qos)
        self.tf_buffer = None
        if tf2_ros is not None:
            self.tf_buffer = tf2_ros.Buffer()
            self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self.node)
        self.node.create_timer(0.1, self.on_timer)
        self.executor = SingleThreadedExecutor()
        self.executor.add_node(self.node)
        self.thread = threading.Thread(target=self.executor.spin, daemon=True)
        self.thread.start()

    def on_battery(self, msg):
        self.battery = (msg.voltage, msg.percentage, time.time())

    def on_scan(self, msg):
        now = time.time()
        valid = sum(1 for r in msg.ranges if math.isfinite(r) and msg.range_min < r < msg.range_max)
        with self.lock:
            self.scan_times.append(now)
            self.scan_valid.append((valid, len(msg.ranges)))
            while self.scan_times and now - self.scan_times[0] > 6.0:
                self.scan_times.pop(0)
                self.scan_valid.pop(0)

    def on_odom(self, msg):
        self.odom_time = time.time()

    def on_map(self, msg):
        with self.lock:
            self.map_msg = msg
            self.map_time = time.time()

    def set_velocity(self, lin, ang):
        lin = max(-CFG['max_lin'], min(CFG['max_lin'], float(lin)))
        ang = max(-CFG['max_ang'], min(CFG['max_ang'], float(ang)))
        with self.lock:
            self.target = (lin, ang)
            self.target_time = time.time()
            self.zero_left = 5
        return lin, ang

    def stop(self):
        with self.lock:
            self.target = (0.0, 0.0)
            self.target_time = 0.0
            self.zero_left = 5
        self.publish(0.0, 0.0)

    def publish(self, lin, ang):
        if self.stamped:
            m = TwistStamped()
            m.header.stamp = self.node.get_clock().now().to_msg()
            m.twist.linear.x = lin
            m.twist.angular.z = ang
        else:
            m = Twist()
            m.linear.x = lin
            m.angular.z = ang
        self.pub.publish(m)

    def on_timer(self):
        with self.lock:
            fresh = time.time() - self.target_time < 0.5
            lin, ang = self.target if fresh else (0.0, 0.0)
            if not fresh:
                if self.zero_left <= 0:
                    return
                self.zero_left -= 1
        self.publish(lin, ang)

    def scan_summary(self):
        with self.lock:
            times, valid = list(self.scan_times), list(self.scan_valid)
        if len(times) < 2 or time.time() - times[-1] > 2.0:
            return {'ok': False, 'hz': 0.0, 'valid': 0, 'total': 0,
                    'text': 'NO llegan mensajes de /scan: revisa el bringup'}
        hz = (len(times) - 1) / (times[-1] - times[0])
        media = sum(v for v, _ in valid) / len(valid)
        total = valid[-1][1]
        problems = []
        if hz < 4:
            problems.append('menos de 4 Hz')
        if media < 150:
            problems.append('pocas medidas validas (prueba el otro LDS_MODEL o una zona con paredes cerca)')
        text = '/scan: %.1f Hz, %.0f de %d medidas validas' % (hz, media, total)
        text += ('. MAL: ' + '; '.join(problems)) if problems else '. OK: puedes empezar a grabar'
        return {'ok': not problems, 'hz': round(hz, 1), 'valid': round(media), 'total': total, 'text': text}

    def robot_pose_px(self, msg):
        if self.tf_buffer is None:
            return None
        try:
            t = self.tf_buffer.lookup_transform(msg.header.frame_id or 'map', 'base_footprint', Time())
        except Exception:
            return None
        r = msg.info.resolution
        o = msg.info.origin.position
        q = t.transform.rotation
        yaw = 2.0 * math.atan2(q.z, q.w)
        px = (t.transform.translation.x - o.x) / r
        py = msg.info.height - 1 - (t.transform.translation.y - o.y) / r
        return px, py, yaw

    def map_png(self):
        with self.lock:
            msg = self.map_msg
        if msg is None:
            return None
        w, h, rows = grid_to_trinary(msg)
        img = [bytearray(r) for r in rows]
        pose = self.robot_pose_px(msg)
        if pose:
            px, py, yaw = pose
            for k in range(0, 9):
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        x = int(round(px + math.cos(yaw) * k * 0.6)) + dx
                        y = int(round(py - math.sin(yaw) * k * 0.6)) + dy
                        if 0 <= x < w and 0 <= y < h:
                            img[y][x] = 1
        return png_bytes(w, h, [bytes(r) for r in img])

    def save_map_internal(self, path_no_ext):
        with self.lock:
            msg = self.map_msg
        if msg is None or time.time() - self.map_time > 30:
            return False
        write_map_files(msg, path_no_ext)
        return True


# ------------------------------------------------------------ procesos

class Proc:
    def __init__(self, name, cmd):
        self.name = name
        self.cmd = cmd
        self.p = None
        self.log_path = os.path.join(CFG['data_dir'], 'log_%s.txt' % name)
        self.started = 0.0

    def running(self):
        return self.p is not None and self.p.poll() is None

    def start(self, cmd=None):
        if self.running():
            return False, '%s ya esta en marcha' % self.name
        log = open(self.log_path, 'w')
        self.p = subprocess.Popen(['bash', '-c', ros_cmd(cmd or self.cmd)], cwd=CFG['data_dir'],
                                  stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        self.started = time.time()
        return True, '%s arrancado' % self.name

    def stop(self, timeout=15):
        if not self.running():
            return False, '%s no estaba en marcha' % self.name
        for sig, wait in ((signal.SIGINT, timeout), (signal.SIGTERM, 5), (signal.SIGKILL, 2)):
            try:
                os.killpg(self.p.pid, sig)
            except ProcessLookupError:
                break
            try:
                self.p.wait(wait)
                break
            except subprocess.TimeoutExpired:
                continue
        return True, '%s parado' % self.name

    def tail(self, n=40):
        try:
            with open(self.log_path, errors='replace') as f:
                return ''.join(f.readlines()[-n:])
        except OSError:
            return ''


class Manager:
    def __init__(self, link):
        self.link = link
        self.procs = {
            'bringup': Proc('bringup', 'ros2 launch turtlebot3_bringup robot.launch.py'),
            'slam': Proc('slam', 'ros2 launch turtlebot3_cartographer cartographer.launch.py '
                                 'use_sim_time:=False use_rviz:=False'),
            'record': Proc('record', ''),
        }
        self.auto_stop = None
        self.auto_thread = None
        self.counter_path = os.path.join(CFG['data_dir'], '.map_counter')
        self.save_lock = threading.Lock()
        self.last_message = ''
        self.current_bag = None
        self.available = {'slam': ros_package_exists('turtlebot3_cartographer') and ros_package_exists('cartographer_ros'),
                          'map_saver': ros_package_exists('nav2_map_server')}

    def external_bringup(self):
        try:
            out = subprocess.run(['pgrep', '-f', 'turtlebot3_bringup|turtlebot3_ros'], capture_output=True, text=True).stdout
        except Exception:
            return False
        ours = set()
        b = self.procs['bringup']
        if b.running():
            try:
                ours = set(subprocess.run(['pgrep', '-g', str(b.p.pid)], capture_output=True, text=True).stdout.split())
            except Exception:
                pass
        return any(pid not in ours for pid in out.split())

    def start(self, name):
        if name == 'bringup':
            if self.external_bringup() and not self.procs['bringup'].running():
                return False, 'Ya hay un bringup lanzado fuera de la app. No lanzo otro: dos a la vez se pelean por los motores y el LIDAR.'
            return self.procs['bringup'].start()
        if name == 'slam':
            if not self.available['slam']:
                return False, 'Cartographer no esta instalado en el robot (turtlebot3_cartographer / cartographer_ros).'
            return self.procs['slam'].start()
        if name == 'record':
            out = 'rosbag_mapping_' + datetime.now().strftime('%Y_%m_%d-%H_%M_%S')
            cmd = 'ros2 bag record -o %s %s' % (out, ' '.join(CFG['record_topics']))
            ok, msg = self.procs['record'].start(cmd)
            if ok:
                self.current_bag = out
            return ok, (msg + ' en ' + os.path.join(CFG['data_dir'], out)) if ok else msg
        if name == 'auto_save':
            return self.start_auto_save()
        return False, 'accion desconocida: ' + name

    def stop(self, name):
        if name == 'auto_save':
            return self.stop_auto_save()
        if name in self.procs:
            return self.procs[name].stop()
        return False, 'accion desconocida: ' + name

    def save_map(self, reset=False):
        with self.save_lock:
            if reset:
                with open(self.counter_path, 'w') as f:
                    f.write('0')
            try:
                with open(self.counter_path) as f:
                    n = int(f.read().strip() or 0)
            except (OSError, ValueError):
                n = 0
            name = 'map_%02d' % n
            path = os.path.join(CFG['data_dir'], name)
            ok = False
            how = ''
            if self.available['map_saver']:
                try:
                    r = subprocess.run(['bash', '-c', ros_cmd('ros2 run nav2_map_server map_saver_cli -f ' + path)],
                                       cwd=CFG['data_dir'], capture_output=True, text=True, timeout=40)
                    ok = r.returncode == 0 and os.path.exists(path + '.pgm')
                    how = 'map_saver_cli'
                except subprocess.TimeoutExpired:
                    ok = False
            if not ok:
                ok = self.link.save_map_internal(path)
                how = 'guardado directo desde /map'
            if ok:
                with open(self.counter_path, 'w') as f:
                    f.write(str(n + 1))
                return True, '%s guardado (%s)' % (name, how)
            return False, 'No se pudo guardar el mapa: no llega /map. Lanza el SLAM primero.'

    def start_auto_save(self, seconds=None, reset=False):
        if self.auto_thread and self.auto_thread.is_alive():
            return False, 'El autoguardado ya esta en marcha'
        seconds = int(seconds or CFG['auto_save_seconds'])
        self.auto_stop = threading.Event()

        def loop():
            ok, msg = self.save_map(reset)
            self.last_message = msg
            while not self.auto_stop.wait(seconds):
                ok, msg = self.save_map()
                self.last_message = msg
            ok, msg = self.save_map()
            self.last_message = 'Ultimo mapa: ' + msg

        self.auto_thread = threading.Thread(target=loop, daemon=True)
        self.auto_thread.start()
        return True, 'Autoguardado cada %d s' % seconds

    def stop_auto_save(self):
        if not (self.auto_thread and self.auto_thread.is_alive()):
            return False, 'El autoguardado no estaba en marcha'
        self.auto_stop.set()
        self.auto_thread.join(60)
        return True, 'Autoguardado parado. ' + self.last_message

    def stop_all(self):
        self.link.stop()
        msgs = []
        if self.auto_thread and self.auto_thread.is_alive():
            msgs.append(self.stop_auto_save()[1])
        for n in ('record', 'slam', 'bringup'):
            if self.procs[n].running():
                msgs.append(self.procs[n].stop()[1])
        return True, ' | '.join(msgs) if msgs else 'No habia nada en marcha'

    def recording_bag(self):
        return self.current_bag if self.procs['record'].running() else None

    def data_items(self):
        d = CFG['data_dir']
        busy = self.recording_bag()
        bags, maps, logs = [], [], []
        for name in sorted(os.listdir(d)):
            path = os.path.join(d, name)
            if os.path.isdir(path) and name.startswith('rosbag'):
                bags.append({'id': name, 'label': name, 'size': tree_size(path), 'busy': name == busy})
            elif name.startswith('map') and name.endswith(('.pgm', '.yaml')):
                maps.append(name)
            elif name.startswith('log_') and name.endswith('.txt'):
                logs.append(name)
        items = []
        if bags:
            items.append({'id': 'all', 'label': 'Todo (bags, mapas y logs)',
                          'size': sum(b['size'] for b in bags if not b['busy']) + files_size(d, maps + logs),
                          'busy': False})
        items.append({'id': 'maps', 'label': 'Mapas y logs (%d mapas)' % (len(maps) // 2),
                      'size': files_size(d, maps + logs), 'busy': False})
        return items + list(reversed(bags))

    def zip_plan(self, item):
        d = CFG['data_dir']
        busy = self.recording_bag()
        plan = []
        for name in sorted(os.listdir(d)):
            path = os.path.join(d, name)
            if os.path.isdir(path) and name.startswith('rosbag'):
                if name == busy or item not in ('all', name):
                    continue
                for root, _, files in os.walk(path):
                    for f in sorted(files):
                        full = os.path.join(root, f)
                        plan.append((full, os.path.relpath(full, d)))
            elif item in ('all', 'maps') and os.path.isfile(path):
                if name.startswith('map') and name.endswith(('.pgm', '.yaml')):
                    plan.append((path, os.path.join('mapas', name)))
                elif name.startswith('log_') and name.endswith('.txt'):
                    plan.append((path, os.path.join('logs', name)))
        return plan

    def info_text(self):
        return ('robot: %s\nfecha: %s\nROS_DOMAIN_ID: %s\nmodelo: %s\nlaser: %s\nros: humble\n'
                % (socket.gethostname(), datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                   CFG['domain_id'], CFG['model'], CFG['lds_model']))

    def status(self):
        b = self.link.battery
        return {
            'robot': socket.gethostname(),
            'domain_id': CFG['domain_id'],
            'running': {n: p.running() for n, p in self.procs.items()},
            'auto_save': bool(self.auto_thread and self.auto_thread.is_alive()),
            'external_bringup': self.external_bringup() and not self.procs['bringup'].running(),
            'available': self.available,
            'battery_v': round(b[0], 2) if b and time.time() - b[2] < 10 else None,
            'odom': time.time() - self.link.odom_time < 2,
            'scan': self.link.scan_summary(),
            'map_age': round(time.time() - self.link.map_time, 1) if self.link.map_msg else None,
            'max_lin': CFG['max_lin'], 'max_ang': CFG['max_ang'],
            'last_message': self.last_message,
            'data_dir': CFG['data_dir'],
        }


def tree_size(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def files_size(d, names):
    return sum(os.path.getsize(os.path.join(d, n)) for n in names if os.path.isfile(os.path.join(d, n)))


# ------------------------------------------------------------------ HTTP

LINK = None
MGR = None


class Handler(BaseHTTPRequestHandler):
    server_version = 'tb3phone/1.2'

    def log_message(self, fmt, *args):
        pass

    def cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Token')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')

    def send_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.cors()
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.cors()
        self.end_headers()

    def authorized(self):
        q = parse_qs(urlparse(self.path).query)
        tok = self.headers.get('X-Token') or (q.get('token') or [''])[0]
        return secrets.compare_digest(str(tok), str(CFG['token']))

    def body(self):
        n = int(self.headers.get('Content-Length') or 0)
        if n <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(n) or b'{}')
        except ValueError:
            return {}

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/ping':
            return self.send_json(200, {'app': 'tb3_phone', 'robot': socket.gethostname()})
        if not self.authorized():
            return self.send_json(401, {'error': 'PIN incorrecto'})
        if path == '/api/status':
            return self.send_json(200, MGR.status())
        if path == '/api/check_scan':
            return self.send_json(200, LINK.scan_summary())
        if path.startswith('/api/log/'):
            name = path.rsplit('/', 1)[-1]
            if name in MGR.procs:
                return self.send_json(200, {'log': MGR.procs[name].tail()})
            return self.send_json(404, {'error': 'no existe'})
        if path == '/api/files':
            return self.send_json(200, {'items': MGR.data_items(), 'recording': MGR.recording_bag()})
        if path == '/api/download':
            return self.send_zip((parse_qs(urlparse(self.path).query).get('item') or ['all'])[0])
        if path == '/api/map.png':
            png = LINK.map_png()
            if png is None:
                return self.send_json(404, {'error': 'todavia no hay mapa'})
            self.send_response(200)
            self.cors()
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', str(len(png)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(png)
            return
        self.send_json(404, {'error': 'no existe'})

    def send_zip(self, item):
        if item == MGR.recording_bag():
            return self.send_json(409, {'error': 'Ese bag se esta grabando. Para la grabacion primero.'})
        plan = MGR.zip_plan(item)
        if item not in ('all', 'maps') and not plan:
            return self.send_json(404, {'error': 'no existe'})
        total = sum(os.path.getsize(f) for f, _ in plan)
        host = socket.gethostname()
        stamp = datetime.now().strftime('%Y_%m_%d-%H_%M_%S')
        fname = '%s_%s.zip' % (host, item if item not in ('all', 'maps') else item + '_' + stamp)
        self.send_response(200)
        self.cors()
        self.send_header('Content-Type', 'application/zip')
        self.send_header('Content-Disposition', 'attachment; filename="%s"' % fname)
        self.send_header('X-File-Name', fname)
        self.send_header('X-Total-Size', str(total))
        self.send_header('Access-Control-Expose-Headers', 'X-File-Name, X-Total-Size')
        self.send_header('Connection', 'close')
        self.end_headers()
        self.close_connection = True
        try:
            with zipfile.ZipFile(self.wfile, 'w', zipfile.ZIP_STORED, allowZip64=True) as z:
                z.writestr('info.txt', MGR.info_text())
                for full, arc in plan:
                    with open(full, 'rb') as src, z.open(arc, 'w', force_zip64=True) as dst:
                        while True:
                            chunk = src.read(1 << 20)
                            if not chunk:
                                break
                            dst.write(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        path = urlparse(self.path).path
        if not self.authorized():
            return self.send_json(401, {'error': 'PIN incorrecto'})
        data = self.body()
        if path == '/api/cmd_vel':
            lin, ang = LINK.set_velocity(data.get('lin', 0.0), data.get('ang', 0.0))
            return self.send_json(200, {'lin': lin, 'ang': ang})
        if path == '/api/stop':
            LINK.stop()
            return self.send_json(200, {'ok': True})
        if path.startswith('/api/start/'):
            name = path.rsplit('/', 1)[-1]
            if name == 'auto_save':
                ok, msg = MGR.start_auto_save(data.get('seconds'), bool(data.get('reset')))
            else:
                ok, msg = MGR.start(name)
            MGR.last_message = msg
            return self.send_json(200, {'ok': ok, 'message': msg})
        if path.startswith('/api/stop/'):
            ok, msg = MGR.stop(path.rsplit('/', 1)[-1])
            MGR.last_message = msg
            return self.send_json(200, {'ok': ok, 'message': msg})
        if path == '/api/save_map':
            ok, msg = MGR.save_map(bool(data.get('reset')))
            MGR.last_message = msg
            return self.send_json(200, {'ok': ok, 'message': msg})
        if path == '/api/shutdown':
            ok, msg = MGR.stop_all()
            subprocess.run(['sync'])
            with open(os.path.join(HERE, '.apagar'), 'w') as f:
                f.write('1')
            msg = 'Apagando el robot. ' + msg
            MGR.last_message = msg
            return self.send_json(200, {'ok': True, 'message': msg})
        if path == '/api/stop_all':
            ok, msg = MGR.stop_all()
            MGR.last_message = msg
            return self.send_json(200, {'ok': ok, 'message': msg})
        self.send_json(404, {'error': 'no existe'})


def main():
    global LINK, MGR
    LINK = RobotLink()
    MGR = Manager(LINK)
    server = ThreadingHTTPServer(('0.0.0.0', int(CFG['port'])), Handler)
    server.daemon_threads = True

    def shutdown(*_):
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    print('tb3_phone_server escuchando en el puerto %d (ROS_DOMAIN_ID=%s, PIN=%s)'
          % (CFG['port'], CFG['domain_id'], CFG['token']), flush=True)
    try:
        server.serve_forever()
    finally:
        MGR.stop_all()
        LINK.executor.shutdown()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
