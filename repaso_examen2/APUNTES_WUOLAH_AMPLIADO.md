# Robótica móvil · Apuntes de examen (ROS 2 Humble · Ubuntu 22.04)

Base: resumen de Natalia Sempere (Wuolah), con sus comandos tal cual. Debajo de los que pueden fallar va un recuadro **Si falla** con la alternativa probada. Ampliado con lo que entra en el examen (QoS, SLAM desde bag, navegación completa y ejercicios de repaso).

---

## 0. Antes de empezar (añadido) <span class="tag e">ENTRA</span>

**Cabecera de todas las terminales y scripts:** <span class="tag e">ENTRA</span>
```bash
#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
```

- **La misma cabecera en todas las terminales**: si una cambia `ROS_LOCALHOST_ONLY` o `ROS_DOMAIN_ID`, no se ven.
- `TURTLEBOT3_MODEL` = el del enunciado (`burger`, `waffle`, `waffle_pi`).
- Simulación o bag → **`use_sim_time:=True`** en SLAM, AMCL, Nav2 (y RViz si se queja: `rviz2 --ros-args -p use_sim_time:=true`).
- Script = cabecera + comando · `chmod +x *.bash` · `./script.bash` desde su carpeta.
- Una terminal por proceso. Al acabar: `Ctrl+C` en cada una. Gazebo colgado: `killall gzserver gzclient`.
- Orden general: **Gazebo → algoritmo (mapa / AMCL / SLAM / Nav2) → RViz → grabación → mover el robot → parar grabación → guardar / zip**.

### Qué entra y qué no

Etiquetas en cada apartado: <span class="tag e">ENTRA</span> lo de los ejercicios de repaso · <span class="tag i">INDIRECTO</span> de prácticas anteriores, por si hay que hacerlo de 0 · <span class="tag n">NO ENTRA</span> robot real o extras.


**Entra directamente** (es lo de los ejercicios de repaso):

| Tema | Sección |
| --- | --- |
| Lanzar Gazebo (house, world, empty, `turtlebot3_no_GUI.launch.py`), modelos burger / waffle_pi | 1 |
| Teleoperar con `teleop_keyboard` | 1 |
| RViz desde cero: displays, QoS, Fixed Frame, guardar `.rviz` | 1 |
| `ros2 bag record / play / info`, `-o`, zip | 1 |
| SLAM en vivo y desde bag: Cartographer, SLAM Toolbox, RTAB-Map | 4 |
| Guardar mapas con `map_saver_cli` | 4 |
| Nav2 con `navigation2.launch.py`, pose inicial, objetivos (RViz y terminal) | 5 |
| RViz de navegación: costmaps, `/plan` | 5 |
| Grabar la navegación y comprobar el bag | 5 |

**Entra indirectamente** (de prácticas anteriores; puede hacer falta montarlo de 0):

| Tema | Sección |
| --- | --- |
| Scripts `.bash` con cabecera, `chmod +x` | 0 |
| Abrir un mapa con `map_server.launch.py` + `lifecycle_manager` | 2 |
| Mapa `.yaml` (resolution, origin) | 2 |
| Transformada estática `map → odom` | 2 |
| Modelo con Building Editor e insertarlo en Gazebo | 2 |
| AMCL: `amcl.launch.py`, pose inicial, partículas | 3 |
| Leer un launch de Gazebo y cambiar mundo y posición | 1 |
| Comparar mapas de SLAM (homework) | 4 |
| Teoría de SLAM y de Nav2 (preguntas cortas) | 4, 5 |

**No entra** (el examen es solo con simulador):
- Robot real: ssh, bringup, `LDS_MODEL`, `ROS_DOMAIN_ID` del laboratorio, WiFi o cable, apagado (secciones 1, 3 y 8 marcadas como robot real).
- Webots: está en el resumen pero no se ha usado en los ejercicios. Si lo piden, los pasos son los mismos que en Gazebo.
- Lo hecho por comodidad: la app del móvil, el autoguardado y la descarga de bags del robot.
- El mapeado del edificio FCS con el robot real (sí cuenta lo que se hace con su bag: reproducirlo y hacer SLAM).

---

## 1. TELEOPERATION <span class="tag e">ENTRA</span>

### TELEOPERATION IN ROS HUMBLE AND GAZEBO <span class="tag e">ENTRA</span>

**ABRIR GAZEBO** <span class="tag e">ENTRA</span>
```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo turtlebot3_house.launch.py
```

**Otros mundos y opciones (añadido)** <span class="tag e">ENTRA</span>
```bash
ros2 launch turtlebot3_gazebo empty_world.launch.py
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
ros2 launch turtlebot3_gazebo empty_world.launch.py x_pose:=1.0 y_pose:=2.0
ros2 launch turtlebot3_no_GUI.launch.py
```
> **Si falla** (`file not found`): el último no es de un paquete, es el fichero del profesor y tiene que estar en la carpeta donde estás. Entrar en ella y lanzar `ros2 launch ./turtlebot3_no_GUI.launch.py`. Carga `turtlebot3_world` con el robot en (-2.0, -0.5), sin ventana.

- Posición inicial por defecto: `empty_world` (0, 0) · `turtlebot3_world` (-2.0, -0.5) · `turtlebot3_house` (-2.0, -0.5).
- **`/odom` de Gazebo está en coordenadas del mundo**: arranca en la posición del robot, no en (0, 0). Por eso los mapas de SLAM y la pose inicial van en esas coordenadas.
- `turtlebot3_world`: hexágono con 9 columnas en x, y ∈ {-1.1, 0, 1.1}.
- **Sin GUI**: solo `gzserver`, no se abre ventana (verla: `gzclient`). Mensajes `Home directory not accessible`, `ALSA`, `AL lib`: normales. Bien si sale `Successfully spawned entity`.
- Launch dado: el mundo es el nombre del `.world` y la posición, los `default` de `x_pose` / `y_pose`.
- `waffle_pi` además publica cámara: `/camera/image_raw`.

**TELEOPERAR** <span class="tag e">ENTRA</span>
```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
ros2 run turtlebot3_teleop teleop_keyboard
```
- `w`/`x` velocidad lineal · `a`/`d` giro · `s` o espacio: parar. Mantiene la velocidad al soltar. La terminal tiene que tener el foco.

**ABRIR RQT** <span class="tag i">INDIRECTO</span>
```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
rqt
```
```bash
sudo apt update
sudo apt install ros-humble-rqt-common-pluggins
```
> **Si falla:** `sudo apt install ros-humble-rqt-common-plugins` (plugins con una sola g).

```text
lauch rqt with –force-discover option
```
> **Si falla:** `rqt --force-discover` (dos guiones normales). `rqt_graph`: nodos y topics.

**GRABACIONES** <span class="tag e">ENTRA</span>
```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 bag record /clock /odom /tf /tf_static
```
```bash
ros2 bag play rosbag2_2024_..
ros2 bag info <bagfile>
```
- **Añadido:**
  - `-o nombre` → carpeta `nombre` en vez de `rosbag2_fecha`. Si ya existe, da error: borrarla o cambiar el nombre.
  - Empezar a grabar **antes** de mover el robot. Parar con `Ctrl+C` **solo al final**; en esa terminal la barra espaciadora **pausa**.
  - `ros2 bag info`: Duration correcta y todos los topics con mensajes. Sin `metadata.yaml` = cortado de golpe.
  - Comprimir: `zip -r nombre.zip nombre` (sin zip: `python3 -m zipfile -c nombre.zip nombre/`).
  - Reproducir con **Gazebo cerrado**. Si el bag ya tiene `/clock`, `play` sin `--clock`.
  - Opciones de `play`: `--rate 2` · `--topics /scan /odom`.

**RQT** <span class="tag e">ENTRA</span>
```bash
rviz2 -d config.rviz
```
> **Ojo:** esto es **RViz**, no rqt. Abre RViz con la configuración guardada.

### RVIZ DESDE CERO (añadido) <span class="tag e">ENTRA</span>

1. `rviz2`
2. **Global Options → Fixed Frame**: `odom` (sin mapa) · `map` (mapa, AMCL, SLAM, Nav2).
3. **Add → By display type** (o By topic).
4. Ajustar topic y **QoS** de cada display.
5. Vista desde arriba: **Views → TopDownOrtho**.
6. **File → Save Config As → `config_xxx.rviz`** · abrir con `rviz2 -d config_xxx.rviz`.

| Display | Topic | QoS / ajuste |
| --- | --- | --- |
| Grid · TF | — | — |
| RobotModel | `/robot_description` | Description Source: Topic · Transient Local |
| Odometry | `/odom` | Reliable |
| LaserScan | `/scan` | Reliability **Best Effort** |
| Image | `/camera/image_raw` | Best Effort (waffle_pi) |
| Map | `/map` | Durability **Transient Local** |
| Map (global costmap) | `/global_costmap/costmap` | Color Scheme **costmap** |
| Map (local costmap) | `/local_costmap/costmap` | Color Scheme **costmap** |
| Path | `/plan` (global) · `/local_plan` | — |
| PoseWithCovariance | `/amcl_pose` | Reliable |
| ParticleCloud | `/particle_cloud` | Best Effort |

- Herramientas: **2D Pose Estimate** → `/initialpose` · **2D Goal Pose / Nav2 Goal** → `/goal_pose`.
- No se ve algo → QoS, Fixed Frame, `use_sim_time`, o el topic no existe (`ros2 topic list`).

### TELEOPERATION IN ROS HUMBLE AND WEBOTS <span class="tag n">NO ENTRA</span>
```bash
sudo apt install ros-humble-webots-ros2
```
```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export WEBOTS_HOME=$HOME/webots-R2023b
ros2 launch webots_ros2_turtlebot robot.launch.py
```
Resto de pasos igual.

### TELEOPERATION WITH PHYSICAL ROBOT <span class="tag n">NO ENTRA</span>
*(Robot real: en el examen de simulador no entra.)*

1) Desktop PC in the laboratory (WiFi and router). WiFi PIROBONET6; tres terminales con `ROS_DOMAIN_ID`.
```bash
ssh ubuntu@192.168.0.xxx
export ROS_DOMAIN_ID=4
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=burger
export LDS_MODEL=LDS-01
ros2 launch turtlebot3_bringup robot.launch.py
```
```bash
export ROS_DOMAIN_ID=4
source /opt/ros/humble/setup.bash
ros2 run turtlebot3_teleop teleop_keyboard
```
```bash
export ROS_DOMAIN_ID=4
source /opt/ros/humble/setup.bash
ros2 bag record /odom /tf /tf_static
```
2) Laptop con Ubuntu 22.04 por WiFi: igual.
3) Laptop por cable: conexión *Link-local*, WiFi apagado, cable, `ip addr` en el robot → IP 169.254.XXX.YYY.
```bash
ssh ubuntu@169.254.xxx.yyy
export ROS_DOMAIN_ID = ...
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=burger
export LDS_MODEL=LDS-01
ros2 launch turtlebot3_bringup robot.launch.py
```
> **Si falla:** sin espacios: `export ROS_DOMAIN_ID=4`. Láser con casi todo a cero → `LDS_MODEL=LDS-02`.

---

## 2. MAPS <span class="tag i">INDIRECTO</span>

**ABRIR RVIZ CONFIGURADO** <span class="tag i">INDIRECTO</span>
```bash
#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
rviz2 -d config_map.rviz
```
- `config_map.rviz`: Fixed Frame `map`, Grid + Map (`/map`, **Transient Local**).

**ABRIMOS EL MAPA EN RVIZ** <span class="tag i">INDIRECTO</span>
```bash
#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 launch map_server.launch.py
```
> **Si falla:** `ros2 launch ./map_server.launch.py` (con `./` si el launch está en la carpeta).

**map_server.launch.py** (versión del resumen)
```python
def generate_launch_description():
    ld = LaunchDescription()
    map_file_path = '../TI_n1.yaml'
    map_server_cmd = Node(
        package='nav2_map_server',
        executable='map_server',
        output='screen',
        parameters=[{'yaml_filename': map_file_path}])
```
> **Si falla** (el mapa no aparece nunca): falta el `lifecycle_manager` que activa el map_server, y la ruta relativa depende de dónde se lance. Launch completo:
> ```python
> import os
> from launch import LaunchDescription
> from launch_ros.actions import Node
>
> def generate_launch_description():
>     yaml = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'TI_n1.yaml')
>     return LaunchDescription([
>         Node(package='nav2_map_server', executable='map_server', output='screen',
>              parameters=[{'yaml_filename': yaml}]),
>         Node(package='nav2_lifecycle_manager', executable='lifecycle_manager', output='screen',
>              parameters=[{'autostart': True, 'node_names': ['map_server']}]),
>     ])
> ```
> Bien si sale «Managed nodes are active». Comprobar: `ros2 topic echo /map --once --field info`.

**El .yaml del mapa (añadido)** <span class="tag i">INDIRECTO</span>
```yaml
image: map.pgm
mode: trinary
resolution: 0.05
origin: [-5.65, -2.02, 0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.25
```
- Imagen: blanco libre · negro obstáculo · gris desconocido.
- `resolution` = metros / píxeles (5 m en 500 px → 0.01). Plano a escala: metros = mm × escala / 1000.
- `origin` = x, y, yaw de la **esquina inferior izquierda**. `image`: relativa al `.yaml`.

**AÑADIMOS TRANSFORMACIONES** <span class="tag i">INDIRECTO</span>
```bash
#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 run tf2_ros static_transform_publisher --x 1 --y 8 --z 0 \
--qx 0 --qy 0 --qz 0 --qw 1 --frame-id map --child-frame-id odom
```
- **Añadido**:
  - x/y = dónde cae el origen del mundo de Gazebo en el frame `map`. Con un mapa de W × H m, `origin [ox, oy]` y el modelo centrado en (Xm, Ym): **x = ox + W/2 − Xm**, **y = oy + H/2 − Ym**.
  - Giro θ: `qz = sin(θ/2)`, `qw = cos(θ/2)` (o `--yaw θ` en radianes).
  - Comprobar con `ros2 run tf2_ros tf2_echo map base_footprint` y viendo que el láser cae sobre las paredes.
  - **Con AMCL o Nav2 no se lanza** (ellos publican `map → odom`).

**ABRIR GAZEBO WORLD + añadir modelo** <span class="tag i">INDIRECTO</span>
```bash
#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo \
empty_world.launch.py
```
- **Modelo con Building Editor (añadido)**:
  1. *Edit → Building Editor* (`Ctrl+B`).
  2. *File → Import* la imagen del mapa → escala con una distancia conocida (o resolución en px/m = 1 / resolution).
  3. *Wall*: clic inicio, doble clic final; `Esc` corta.
  4. *File → Save As* con nombre (crea `model.config` + `model.sdf`) → *Exit Building Editor*.
  5. Insertar: *Insert → Add Path* → carpeta que contiene el modelo → clic y colocar.
- Alternativa: `ros2 run gazebo_ros spawn_entity.py -entity rooms -file models/rooms/model.sdf -x 0 -y 0 -z 0`
- `model.config` con `<name>` correcto (no «Untitled»). Entregar: `zip -r rooms.zip rooms`.

**TELEOPERAR** <span class="tag e">ENTRA</span> (igual que en 1)

**GRABACIÓN DURANTE 60 SEGUNDOS** <span class="tag i">INDIRECTO</span>
```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 bag record /clock /map /odom /scan /tf /tf_static
```
- **Añadido**: para ver el robot al reproducir, añadir `/robot_description`.

**ABRIMOS RVIZ PARA MOSTRAR LA GRABACIÓN** <span class="tag i">INDIRECTO</span>: `./visualize_map.bash` + `ros2 bag play rosbag2_2024_..`

**Con robot físico**: mismos pasos cambiando `ROS_LOCALHOST_ONLY` por `ROS_DOMAIN_ID`; grabar `/map /odom /scan /tf /tf_static`.

---

## 3. LOCALIZATION <span class="tag i">INDIRECTO</span>

### LOCALIZATION IN SIMULATION <span class="tag i">INDIRECTO</span>

**ABRIR GAZEBO** <span class="tag i">INDIRECTO</span>
```bash
#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=4
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo \
empty_world.launch.py
```
> **Si falla** (los nodos no se ven): en simulación usar la misma cabecera que en el resto de terminales: `export ROS_LOCALHOST_ONLY=1` en todas (o el mismo `ROS_DOMAIN_ID` en todas). El resumen mezcla `ROS_DOMAIN_ID=4`, `=9` y `ROS_LOCALHOST_ONLY=1`.

Dentro de Gazebo, insertamos el modelo (en path).

**AÑADIMOS EL AMCL** <span class="tag i">INDIRECTO</span>
```bash
#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=4
export TURTLEBOT3_MODEL=burger
ros2 launch amcl.launch.py \
use_sim_time:=True \
map:=../TD_n1.yaml
```
> **Si falla:** misma cabecera que las demás terminales; mapa con ruta absoluta `map:=$PWD/TD_n1.yaml`; y `ros2 launch ./amcl.launch.py` si está en la carpeta.

**amcl.launch.py (añadido, por si hay que escribirlo)** <span class="tag i">INDIRECTO</span>
```python
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    params = os.path.join(get_package_share_directory('turtlebot3_navigation2'), 'param', 'humble', 'burger.yaml')
    bringup = os.path.join(get_package_share_directory('nav2_bringup'), 'launch', 'bringup_launch.py')
    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(bringup),
            launch_arguments={'map': LaunchConfiguration('map'),
                              'use_sim_time': LaunchConfiguration('use_sim_time'),
                              'params_file': params}.items()),
    ])
```
> **Si falla** (no encuentra el `.yaml`): `ls /opt/ros/humble/share/turtlebot3_navigation2/param/`. Si no hay carpeta `humble/`, la ruta es `'param', 'burger.yaml'`. La clave es `params_file`, no `params`.

**INICIAMOS RVIZ** <span class="tag i">INDIRECTO</span>
```bash
#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
rviz2 -d config_amcl.rviz
```
- `config_amcl.rviz`: Fixed Frame `map`; Grid, RobotModel, TF, LaserScan, Map, PoseWithCovariance (`/amcl_pose`), Odometry, ParticleCloud (`/particle_cloud`).

Y agregamos **2D Pose Estimate**, donde iniciamos el Gazebo.
- **Pose inicial por terminal (añadido)**:
```bash
ros2 topic pub -t 3 -r 2 /initialpose geometry_msgs/msg/PoseWithCovarianceStamped "{header: {frame_id: map}, pose: {pose: {position: {x: 2.5, y: 2.5}, orientation: {w: 1.0}}}}"
```
- x, y = posición del robot en el frame `map`. Comprobar: `ros2 topic echo /amcl_pose --once`.
- Antes de la pose salen avisos «Please set the initial pose»: normal.

**TELEOPERAMOS EL ROBOT** <span class="tag e">ENTRA</span>
```bash
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=9
export TURTLEBOT3_MODEL=burger
ros2 run turtlebot3_teleop teleop_keyboard
```
> **Si falla** (no se mueve): misma cabecera que Gazebo (`ROS_DOMAIN_ID` igual en todas, o `ROS_LOCALHOST_ONLY=1` en todas).

**GRABAMOS** <span class="tag i">INDIRECTO</span>
```bash
source /opt/ros/humble/setup.bash
ros2 bag record /clock /map /odom /scan /tf /tf_static /amcl_pose
/particle_cloud /robot_description
```
> **Si falla:** todo en una línea (o con `\` al final), y con la misma cabecera que el resto (añadir `export ROS_LOCALHOST_ONLY=1`).

### LOCALIZATION WITH THE PHYSICAL ROBOT <span class="tag n">NO ENTRA</span>
*(Robot real: no entra en simulación.)*
```bash
export ROS_DOMAIN_ID = ...
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch amcl.launch.py \
use_sim_time:=True \
map:=../TI_n1_edited.yaml
```
> **Si falla:** `export ROS_DOMAIN_ID=4` sin espacios; con robot real `use_sim_time:=False`.

Grabar 1–3 min: `ros2 bag record /map /odom /scan /tf /tf_static /amcl_pose /particle_cloud /robot_description`

---

## 4. SLAM METHODS - CARTOGRAPHER <span class="tag e">ENTRA</span>

```bash
sudo apt install ros_humble-turtlebot3-cartographer
```
> **Si falla:** `sudo apt install ros-humble-turtlebot3-cartographer` (con guiones).

**Terminal 1 - Launch the house simulation** <span class="tag e">ENTRA</span>
```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo turtlebot3_house.launch.py
```

**Terminal 2 - Teleoperation** <span class="tag e">ENTRA</span>
```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
ros2 run turtlebot3_teleop teleop_keyboard
```

**Terminal 3 - Abrir RViZ Cartographer** <span class="tag e">ENTRA</span>
```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_cartgrapher cartographer.launch.py use_sim_time:=True
```
> **Si falla:** `ros2 launch turtlebot3_cartographer cartographer.launch.py use_sim_time:=True` (carto**grapher** con «o»).

**Terminal 4 - Grabar** <span class="tag e">ENTRA</span>
```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 bag record /clock /map /map_updates /odom /robot_description /scan /scan_matched_points2 /submap_list /tf /tf_static
```

**Terminal 5 - Save map** <span class="tag e">ENTRA</span>
```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 run nav2_map_server map_server_cli -f ./map
```
> **Si falla:** `ros2 run nav2_map_server map_saver_cli -f ./map` (map_**saver**). Si se queda esperando: añadir `--ros-args -p use_sim_time:=true` o `-p map_subscribe_transient_local:=false`. Guarda lo que hay en `/map` en ese momento: el SLAM tiene que seguir abierto. Ir cambiando el nombre: `map1`, `map2`…

**Terminal 6 - Verificar** <span class="tag e">ENTRA</span>
```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
rviz2 -d /opt/ros/humble/share/turtlebot3_cartographer/rviz/tb3_cartographer.rviz
```
+ `ros2 bag play` en otra terminal.

### OTHERS SLAM ALGORITHM <span class="tag e">ENTRA</span>

**ROS2 SLAM TOOLBOX** <span class="tag e">ENTRA</span>
```bash
sudo apt install ros-humble-slam-toolbox
ros2 launch slam_toolbox online_async_launch.py use_sim_time:=True
```

**RTAB-MAP** <span class="tag e">ENTRA</span>
```bash
sudo apt install ros-humble-rtabmap-ros
ros2 launch rtabmap_demos turtlebot3_scan.launch.py use_sim_time:=True
```
> **Si falla** (no guarda mapa): RTAB-Map solo publica `/map` si alguien lo escucha → tener RViz abierto con el display Map. Si el launch no existe, lanzar el nodo solo con láser:
> ```bash
> ros2 run rtabmap_slam rtabmap --delete_db_on_start --ros-args -p use_sim_time:=true -p frame_id:=base_footprint -p odom_frame_id:=odom -p subscribe_depth:=false -p subscribe_rgb:=false -p subscribe_scan:=true -p approx_sync:=true -p Reg/Strategy:="'1'" -p Reg/Force3DoF:="'true'" -p Grid/Sensor:="'0'" -r scan:=/scan
> ```

- SLAM Toolbox y RTAB-Map no abren RViz: abrir uno con Map (`/map`, Transient Local), LaserScan, RobotModel y Fixed Frame `map`.
- Todos publican `/map` y `map → odom`.

### SLAM DESDE UN BAG (añadido · ejercicio de repaso) <span class="tag e">ENTRA</span>

1. **Gazebo cerrado** (si no: dos `/clock` y dos `/tf`).
2. **1º lanzar el SLAM**, **2º `ros2 bag play nombre_bag`** (al revés se pierde `/tf_static`).
3. Mientras se reproduce: `map_saver_cli -f maps/map_<alg>_N` repartidos por la duración (bag de T s → uno cada T/N; el último al acabar).
4. `Ctrl+C` al SLAM y repetir con el siguiente algoritmo.
5. `zip -r maps.zip maps`
- Topics que tiene que tener el bag para hacer SLAM: `/clock /odom /scan /tf /tf_static /robot_description`.

### TEORÍA SLAM (añadido, diapositivas) <span class="tag i">INDIRECTO</span>
- **SLAM**: con controles y observaciones, estimar a la vez el estado del robot y el mapa (probabilístico).
- **Cartographer**: *local SLAM* (frontend) construye submapas por scan matching, con el *pose extrapolator* (odometría/IMU) como estimación inicial; deriva. *Global SLAM* (backend) busca **cierres de bucle** y reordena submapas. Filtro paso banda de distancias (min–max).
- **SLAM Toolbox** (Macenski): grafo de poses + scan matching. **RTAB-Map** (Labbé): grafo con gestión de memoria y bucles; láser y/o visual.
- Mapas típicos: Cartographer paredes nítidas con zonas grises · SLAM Toolbox cubre bien con dientes de sierra · RTAB-Map el más limpio.

---

## 5. NAVIGATION <span class="tag e">ENTRA</span>

**Terminal 1 - Primero actualizar burger.yaml** <span class="tag i">INDIRECTO</span>
```bash
ls /opt/ros/humble/share
sudo mv /Descargas/burger.yaml
/opt/ros/humble/share/turtlebot3_navigation2/param
```
> **Si falla:** todo en una línea y con la carpeta personal: `sudo mv ~/Descargas/burger.yaml /opt/ros/humble/share/turtlebot3_navigation2/param/`. Solo si el enunciado da ese fichero. Ver qué hay: `ls /opt/ros/humble/share/turtlebot3_navigation2/param/` (si existe `humble/`, los de Humble están ahí).

**Terminal 2 - Abrir Gazebo** <span class="tag e">ENTRA</span>
```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo turtlebot3_house.launch.py
```

**Terminal 3 - Abrir RViZ con Mapa** <span class="tag e">ENTRA</span>
```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True map:=map7.yaml
```
> **Si falla** (no encuentra el mapa): ruta absoluta `map:=$PWD/map7.yaml`. Ver argumentos: `--show-args`. Sin su RViz: `ros2 launch nav2_bringup bringup_launch.py use_sim_time:=True map:=$PWD/map7.yaml params_file:=<ruta>/burger.yaml`.

- **Añadido**: Nav2 = `map_server` + `amcl` + planner (ruta global `/plan`) + controller (ruta local `/local_plan`, publica `/cmd_vel`) + costmaps (global: todo el mapa; local: alrededor del robot; capas static / obstacle / inflation) + bt_navigator + lifecycle_manager. Espera «Managed nodes are active».

**Terminal 4 - Coordenadas (modificarlas hasta que cuadre)** <span class="tag i">INDIRECTO</span>
```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
./publish_transform.bash
```
> **Si falla** (TF que salta, robot que se teletransporta en RViz): con Nav2 normalmente **no** hace falta, porque AMCL ya publica `map → odom` → cerrar esta terminal y dar la **pose inicial** en su lugar:
> - RViz: **2D Pose Estimate** donde está el robot, arrastrando hacia donde mira.
> - Terminal: `ros2 topic pub -t 3 -r 2 /initialpose geometry_msgs/msg/PoseWithCovarianceStamped "{header: {frame_id: map}, pose: {pose: {position: {x: -2.0, y: -0.5}, orientation: {w: 1.0}}}}"`
> - Si el mapa salió de un SLAM en la misma simulación, las coordenadas son las de Gazebo (house y world: -2.0, -0.5).

**Terminal 5 - Abrir la grabación** <span class="tag e">ENTRA</span>
```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
ros2 bag record /clock /tf /tf_static /map /robot_description /scan /particle_cloud /plan /local_plan /waypoints /mobile_base/sensors/bumper_pointcloud /global_costmap/costmap /global_costmap/costmap_updates /global_costmap/voxel_marked_cloud /downsampled_costmap /downsampled_costmap_updates /local_costmap/costmap /local_costmap/costmap_updates /local_costmap/published_footprint /local_costmap/voxel_marked_cloud
```
> **Si falla** (o faltan topics en `bag info`): algunos son de TurtleBot2 y en TurtleBot3 no existen (no dan error, simplemente no graban). Lista para TurtleBot3:
> `ros2 bag record /clock /tf /tf_static /map /robot_description /scan /odom /amcl_pose /particle_cloud /plan /local_plan /cmd_vel /global_costmap/costmap /local_costmap/costmap`

**Terminal 6 - Teleoperar** <span class="tag e">ENTRA</span> (o mandar objetivos, abajo)
```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
ros2 run turtlebot3_teleop teleop_keyboard
```

**Objetivos (añadido)** <span class="tag e">ENTRA</span>
- RViz: **Nav2 Goal / 2D Goal Pose** → clic + arrastrar la orientación. Varios: panel Navigation 2 → *Waypoint / Nav Through Poses Mode*.
- Terminal (espera a que llegue):
```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: map}, pose: {position: {x: 0.55, y: 0.55}, orientation: {w: 1.0}}}}"
```
- Objetivos en zona libre, lejos de paredes. Orientación θ: `z = sin(θ/2)`, `w = cos(θ/2)` → 0° `{w: 1}` · 90° `{z: 0.707, w: 0.707}` · 180° `{z: 1, w: 0}`.
- Puntos libres en `turtlebot3_world`: (-0.55, -0.55) · (0.55, 0.55) · (1.6, -0.5) · (0.55, -0.55) · (-2.0, -0.5).
- No se mueve → falta pose inicial u objetivo en zona ocupada / desconocida.

**RViz de navegación (añadido)** <span class="tag e">ENTRA</span>: Map + Map global costmap + Map local costmap (Color Scheme costmap) + Path `/plan` + LaserScan + RobotModel + TF · Fixed Frame `map` → *Save Config As* `nav2_view.rviz`.

**Terminal 7 - Verificar** <span class="tag e">ENTRA</span>
```bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
rviz2 -d /opt/ros/humble/share/nav2_bringup/rviz/nav2_default_view.rviz
```
```bash
ros2 bag play rosbag2_2024...
```

---

## 6. EJERCICIOS DE REPASO RESUELTOS (añadido) <span class="tag e">ENTRA</span>

Con `TURTLEBOT3_MODEL=waffle_pi` y `turtlebot3_no_GUI.launch.py` en la carpeta.

**Teleoperation and recording** <span class="tag e">ENTRA</span> → `config_teleop.rviz` + `rosbag_teleop.zip`
1. T1 `ros2 launch turtlebot3_no_GUI.launch.py`
2. T2 `rviz2` → Odometry, LaserScan (Best Effort), RobotModel, Image, TF · Fixed Frame `odom` → guardar `config_teleop.rviz`
3. T3 `ros2 bag record -o rosbag_teleop /clock /odom /scan /tf /tf_static /robot_description`
4. T4 teleop 3–5 min → `Ctrl+C` en T3 → `ros2 bag info rosbag_teleop` → `zip -r rosbag_teleop.zip rosbag_teleop`

**SLAM** <span class="tag e">ENTRA</span> → `config_slam.rviz` + `maps.zip`
1. RViz anterior + Map (`/map`, Transient Local) · Fixed Frame `map` → guardar `config_slam.rviz`
2. Gazebo cerrado. Para cada algoritmo: lanzarlo → `ros2 bag play rosbag_teleop` → 5 × `ros2 run nav2_map_server map_saver_cli -f maps/map_<alg>_N` → `Ctrl+C`
3. Nombres `map_slam_toolbox_N`, `map_cartographer_N`, `map_rtabmap_N` → `zip -r maps.zip maps`

**Navigation** <span class="tag e">ENTRA</span> → `nav2_view.rviz` + `rosbag_nav.zip`
1. T1 simulación recién lanzada · T2 `ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True map:=$PWD/maps/map_rtabmap_5.yaml`
2. RViz con costmaps y Path → guardar `nav2_view.rviz`
3. Pose inicial (-2.0, -0.5) → `ros2 bag record -o rosbag_nav …` (lista TB3) → 5 objetivos → `Ctrl+C` → `zip -r rosbag_nav.zip rosbag_nav`

---

## 7. DIAGNÓSTICO Y PROBLEMAS (añadido) <span class="tag e">ENTRA</span>

```bash
ros2 topic list
ros2 topic info -v /scan
ros2 topic hz /scan
ros2 topic echo /odom --once
ros2 topic echo /map --once --field info
ros2 node list
ros2 run tf2_ros tf2_echo map base_footprint
ros2 run tf2_tools view_frames
ros2 bag info carpeta_bag
ros2 pkg prefix nombre_paquete
ros2 launch paquete fichero.launch.py --show-args
ros2 interface show geometry_msgs/msg/PoseWithCovarianceStamped
ros2 action list
```
- Árbol TF: `map → odom → base_footprint → base_link → base_scan` (map→odom: SLAM / AMCL / transformada; odom→base: Gazebo; resto: robot_state_publisher).

| Problema | Solución |
| --- | --- |
| Terminales que no se ven | misma cabecera en todas |
| `KeyError: TURTLEBOT3_MODEL` / no aparece el robot | `export TURTLEBOT3_MODEL=…` |
| Gazebo no arranca, «/spawn_entity unavailable» | `killall gzserver gzclient` |
| LaserScan / Image no se ven | QoS Best Effort |
| El mapa no aparece | Transient Local; map_server sin lifecycle_manager |
| «Fixed Frame [map] does not exist» | falta mapa+transformada, AMCL sin pose inicial, o SLAM sin lanzar |
| SLAM no hace nada con el bag | falta `use_sim_time:=True` o se lanzó después del bag |
| Saltos raros al reproducir | Gazebo sigue abierto |
| `map_saver_cli` no guarda | `use_sim_time`, `map_subscribe_transient_local:=false`, RViz con Map |
| La grabación dura segundos | `Ctrl+C` o espacio en su terminal |
| «already exists» al grabar | borrar la carpeta o cambiar `-o` |
| AMCL con partículas por todo el mapa | pose inicial mal o robot movido antes |
| Nav2 no se mueve | falta pose inicial u objetivo en zona ocupada |
| Dos `map_server` / TF que salta | cerrar `publish_map` / transformada con AMCL o Nav2 |
| `Permission denied` | `chmod +x *.bash` |

---

## 8. EXTRAS ENRIC - Connecting to the TurtleBot 3 <span class="tag n">NO ENTRA</span>
*(Robot real: no entra en simulación.)*

1. Batería → encender → esperar un minuto → `ssh ubuntu@192.168.0.xxx` (si pregunta, `yes`; contraseña `turtlebot`).
2. Bringup:
   - Robots 101-110: `TURTLEBOT3_MODEL=burger`, `LDS_MODEL=LDS-01`, `ROS_DOMAIN_ID=1…10`
   - Robots 111-112: `TURTLEBOT3_MODEL=waffle_pi`, `LDS_MODEL=LDS-01`, `ROS_DOMAIN_ID=11/12`
   - Robots 202-206: `source ~/ros2_ws/install/setup.bash`, `burger`, `LDS-02`, `ROS_DOMAIN_ID=22…26`
   - `ros2 launch turtlebot3_bringup robot.launch.py`
3. Apagar: `Ctrl+C` al bringup → `sudo halt -p` → esperar a que el LED amarillo deje de parpadear → apagar → quitar batería.
