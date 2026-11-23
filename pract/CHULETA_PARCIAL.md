# Chuleta parcial IR2121 — hasta Localization (ROS 2 Humble, simulación)

Todos los ficheros en la misma carpeta. Los `.bash`: `chmod +x *.bash` y se lanzan con `./nombre.bash`. Cada uno en su terminal. Una `\` al final de una línea de bash significa que el comando sigue en la línea siguiente.

## 0. Cabecera (va en todos los .bash)

```bash
#!/bin/bash
cd "$(dirname "$(readlink -f "$0")")"
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
```

- `cd ...`: se mete en la carpeta del script → funciona lo lances desde donde lo lances.
- `source`: carga ROS 2. `ROS_LOCALHOST_ONLY=1`: igual en todas las terminales o no se ven.
- `TURTLEBOT3_MODEL`: solo hace falta en Gazebo y teleop; en los demás no molesta.

## 1. Maps

**rooms.yaml** (5 m entre 500 px → 5/500 = 0.01 m/px)

```yaml
image: rooms.png
mode: trinary
resolution: 0.01
origin: [0.0, 0.0, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.25
```

- `origin`: x, y, yaw de la esquina inferior izquierda de la imagen. Tamaño de la imagen: `file rooms.png`.

**map\_server.launch.py**

```python
import os
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    yaml = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'rooms.yaml')
    return LaunchDescription([
        Node(package='nav2_map_server', executable='map_server', output='screen',
             parameters=[{'yaml_filename': yaml}]),
        Node(package='nav2_lifecycle_manager', executable='lifecycle_manager', output='screen',
             parameters=[{'autostart': True, 'node_names': ['map_server']}]),
    ])
```

- `yaml = ...`: ruta absoluta a `rooms.yaml`, en la misma carpeta que el launch.
- `map_server`: publica `/map`. `lifecycle_manager`: lo activa; sin él no se publica nunca.

**publish\_map.bash**: cabecera + `ros2 launch ./map_server.launch.py`

**visualize\_map.bash**: cabecera + `rviz2 -d config_map.rviz`

**config\_map.rviz**: `rviz2` → Fixed Frame `map` → Add *Map* (topic `/map`, Durability **Transient Local**) → *File → Save Config As* `config_map.rviz`.

Comprobar: `ros2 topic echo /map --once --field info` → 0.01, 500, 500, origen 0 0.

## 2. Simulation

**launch\_tb3\_empty\_sim.bash**: cabecera + estas dos líneas:

```bash
export GAZEBO_MODEL_PATH="$PWD/models:$GAZEBO_MODEL_PATH"
ros2 launch turtlebot3_gazebo empty_world.launch.py
```

- `GAZEBO_MODEL_PATH`: así `rooms` sale en la pestaña *Insert* de Gazebo.

**Building Editor**

1. `./launch_tb3_empty_sim.bash` → *Edit → Building Editor* (`Ctrl+B`).
2. *File → Import* → `rooms.png` → *Next* → escala: clic en los dos extremos del borde y escribir 5 m (o Resolution = 100 px/m).
3. *Wall*: clic al inicio y doble clic al final de cada pared. `Esc` corta.
4. *File → Save As*: nombre `rooms`, carpeta `models/` → crea `models/rooms/model.config` y `model.sdf`.
5. *File → Exit Building Editor*. Comprobar `<name>rooms</name>` en `model.config`.

**insert\_rooms.bash**: cabecera + esta línea (o *Insert* → `rooms` → colocarlo en 0, 0):

```bash
ros2 run gazebo_ros spawn_entity.py -entity rooms -file models/rooms/model.sdf \
  -x 0 -y 0 -z 0
```

**rooms.zip**: `cd models && zip -r ../rooms.zip rooms` (sin zip: `python3 -m zipfile -c ../rooms.zip rooms/`).

## 3. Teleoperation

**publish\_transform.bash**: cabecera + este comando:

```bash
ros2 run tf2_ros static_transform_publisher --x 2.5 --y 2.5 --z 0 \
  --qx 0 --qy 0 --qz 0 --qw 1 --frame-id map --child-frame-id odom
```

- Es dónde cae el (0, 0) de Gazebo en el mapa: x = ox + W/2 − Xm = 0 + 2.5 − 0. No depende de dónde nazca el robot.
- Si el mapa estuviera girado θ: `--yaw θ` en radianes, en vez de qz/qw.

**visualize\_robot.bash**: cabecera + `rviz2 -d config_robot.rviz`

**config\_robot.rviz**: Fixed Frame `odom` → Add: *Map* (`/map`, Transient Local), *Odometry* (`/odom`), *LaserScan* (`/scan`, Best Effort), *RobotModel* (Description Topic `/robot_description`, Transient Local) → Save Config As.

**Terminales**

1. `./launch_tb3_empty_sim.bash`
2. `./insert_rooms.bash`
3. `./publish_map.bash`
4. `./publish_transform.bash`
5. `./visualize_robot.bash` → el láser verde tiene que caer sobre las paredes
6. `ros2 bag record /map /clock /tf /tf_static /robot_description /odom /scan`
7. `ros2 run turtlebot3_teleop teleop_keyboard` → `w`/`x` velocidad, `a`/`d` giro, `s` parar; visitar las 4 habitaciones
8. `Ctrl+C` en la 6 → `ros2 bag info rosbag2_...` → `zip -r rosbag.zip rosbag2_.../`

## 4. Localization

Cerrar `publish_map` y `publish_transform`: AMCL publica él solo el mapa y map → odom. Relanzar Gazebo para que el robot vuelva a (0, 0).

**amcl.launch.py**

```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    params = os.path.join(get_package_share_directory('turtlebot3_navigation2'),
                          'param', 'humble', 'burger.yaml')
    bringup = os.path.join(get_package_share_directory('nav2_bringup'),
                           'launch', 'bringup_launch.py')
    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(bringup),
            launch_arguments={'map': LaunchConfiguration('map'),
                              'use_sim_time': LaunchConfiguration('use_sim_time'),
                              'params_file': params}.items()),
    ])
```

- `params`: parámetros del burger para Humble (`param/humble/`, no `param/burger.yaml`).
- Si `ls /opt/ros/humble/share/turtlebot3_navigation2/param/` no tiene carpeta `humble/`, usar `'param', 'burger.yaml'`.
- `bringup`: lanza nav2 entero (map\_server + AMCL + navegación).
- `map` y `use_sim_time` los pasa `launch_amcl.bash`.

**launch\_amcl.bash**: cabecera + esta línea:

```bash
ros2 launch ./amcl.launch.py use_sim_time:=True map:=$PWD/rooms.yaml
```

- `$PWD/rooms.yaml`: ruta absoluta. `use_sim_time:=True` porque es simulación.

**visualize\_localization.bash**: cabecera + `rviz2 -d config_amcl.rviz`

**config\_amcl.rviz**: Fixed Frame `map` → Add: *RobotModel* (Transient Local), *TF*, *LaserScan* (Best Effort), *Map* (Transient Local), *PoseWithCovariance* (`/amcl_pose`), *Odometry* (`/odom`), *ParticleCloud* (`/particle_cloud`, Best Effort) → Save Config As.

**Pose inicial** (robot en 2.5, 2.5 del mapa, mirando a +x): *2D Pose Estimate* en RViz, o por terminal:

```bash
ros2 topic pub -w 1 -t 3 /initialpose geometry_msgs/msg/PoseWithCovarianceStamped \
  "{header: {frame_id: map}, pose: {pose: {position: {x: 2.5, y: 2.5}, orientation: {w: 1.0}}}}"
```

**Terminales**

1. `./launch_tb3_empty_sim.bash`
2. `./insert_rooms.bash`
3. `./visualize_localization.bash` (antes que AMCL)
4. `./launch_amcl.bash` → esperar «Managed nodes are active»; los «Timed out waiting for transform... map» son normales hasta dar la pose
5. Pose inicial (sin mover el robot antes) → en AMCL sale «Setting pose: 2.500 2.500»
6. `ros2 bag record /map /clock /tf /tf_static /robot_description /amcl_pose /particle_cloud /odom /scan`
7. Teleop → la nube se concentra en el robot
8. `Ctrl+C` en la 6 → `ros2 bag info` → `zip -r`

## 5. Si algo falla

| Síntoma | Solución |
| --- | --- |
| RViz no pinta el mapa | Map → Durability **Transient Local** |
| No sale el láser | LaserScan → Reliability **Best Effort** |
| «Fixed Frame [map] does not exist» | Falta `publish_transform` o la pose inicial de AMCL |
| AMCL: «Failed to change state for node: map\_server» | Hay un `publish_map` abierto: cerrarlo y relanzar AMCL |
| Gazebo no abre / «/spawn\_entity unavailable» | `killall gzserver gzclient` (o `pkill -9 gzserver`) |
| `Permission denied` | `chmod +x *.bash` |
| Los nodos no se ven | Misma cabecera en todas las terminales |
| Bag sin `metadata.yaml` | Parar siempre con `Ctrl+C` |

Comprobaciones: `ros2 topic list`, `ros2 topic hz /scan`, `ros2 run tf2_ros tf2_echo map base_footprint` (robot quieto en rooms → 2.5, 2.5), `ros2 launch <pkg> <fichero> --show-args`.
