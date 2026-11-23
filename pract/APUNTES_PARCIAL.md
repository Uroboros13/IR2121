# Apuntes parcial IR2121 — Simulación (ROS 2 Humble)

Oct 25, 2026 · @Buguisoft

## 1. Entorno y cabecera común

En simulación todas las terminales llevan la misma cabecera: si una sola cambia `ROS_LOCALHOST_ONLY` o pone un `ROS_DOMAIN_ID` distinto, los nodos no se ven entre sí.

```bash
#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
```

- `TURTLEBOT3_MODEL` solo hace falta en Gazebo, teleop y AMCL; en el resto no molesta.
- Robot físico: se quita `ROS_LOCALHOST_ONLY` y se pone `export ROS_DOMAIN_ID=N` (sin espacios alrededor del `=`). En el parcial no cae.
- Scripts nuevos: `chmod +x *.bash` y se lanzan con `./nombre.bash` desde su carpeta.
- Rutas relativas (`../mapa.yaml`) se resuelven desde la carpeta donde lanzas el comando, no desde donde está el fichero.
- Cada proceso en su terminal: Gazebo, mapa, transformada, RViz, teleop y grabación van separados.
- Al acabar o si algo se cuelga: `Ctrl+C` en cada terminal y `killall gzserver gzclient`. Si no existe `killall` (paquete `psmisc`): `pkill -9 gzserver; pkill -9 gzclient`.

Orden general de una práctica: **1** Gazebo → **2** insertar modelo → **3** mapa (o AMCL) → **4** transformada (solo sin AMCL) → **5** RViz → **6** grabación → **7** teleop.

## 2. Teleoperación en Gazebo y rosbags

Gazebo, teleop y grabación van en tres terminales, todas con la cabecera de la sección 1.

```bash
ros2 launch turtlebot3_gazebo empty_world.launch.py
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
ros2 launch turtlebot3_gazebo turtlebot3_house.launch.py
```

- `empty_world` pone el robot en (0, 0) de Gazebo. Acepta `x_pose:=1.0 y_pose:=2.0` para colocarlo en otro sitio. `/odom` da la posición respecto al origen del mundo de Gazebo: con `x_pose:=1.0 y_pose:=2.0` el odom arranca en (1, 2), no en (0, 0).
- Teleop: `ros2 run turtlebot3_teleop teleop_keyboard` → `w`/`x` aceleran o frenan, `a`/`d` giran, `s` o espacio para. La terminal del teleop tiene que tener el foco.
- rqt: `rqt` (si faltan plugins: `rqt --force-discover`). `rqt_graph` muestra nodos y topics.

**Rosbags**

```bash
ros2 bag record /clock /odom /tf /tf_static
ros2 bag record -o nombre_bag /clock /odom /tf /tf_static
ros2 bag info rosbag2_2026_...
ros2 bag play rosbag2_2026_...
zip -r rosbag.zip rosbag2_2026_.../
```

- Se empieza a grabar **antes** de mover el robot y se para con `Ctrl+C` en la terminal de grabación.
- En simulación siempre se graba `/clock`.
- Sin `-o` la carpeta se llama `rosbag2_AAAA_MM_DD-hh_mm_ss`; con `-o nombre_bag` se llama `nombre_bag` (y el `.db3`, `nombre_bag_0.db3`).
- La carpeta del bag debe tener `metadata.yaml` y el `.db3`. Si falta el `metadata.yaml`, la grabación se cortó mal.
- Si no está `zip`: `python3 -m zipfile -c rosbag.zip rosbag2_2026_.../` (mete la carpeta entera; se comprueba con `python3 -m zipfile -l rosbag.zip`).
- Antes de entregar: `ros2 bag info` → todos los topics con mensajes y la duración esperada.
- Para ver el bag: `ros2 bag play` en una terminal y RViz con su config en otra; Gazebo cerrado.

## 3. RViz desde cero

Una config de RViz se crea a mano y se guarda con *File → Save Config As* (`config_map.rviz`, `config_robot.rviz`, `config_amcl.rviz`). Después se abre con `rviz2 -d config_xxx.rviz`.

1. `rviz2` (con la cabecera).
2. *Global Options → Fixed Frame*: `map` (mapa y AMCL) u `odom` (solo odometría o teleop con transformada). Se escribe a mano si no aparece en la lista.
3. *Add → By topic* (o *By display type*) y añadir los displays de la tabla.
4. Ajustar la QoS en *Topic* de cada display.
5. Vista desde arriba: *Views → Type: TopDownOrtho*.
6. *File → Save Config As*.

| Display | Topic | QoS que hay que poner | Práctica |
| --- | --- | --- | --- |
| Grid | — | — | todas |
| Map | `/map` | Durability **Transient Local** | Maps, Teleop, AMCL |
| Odometry | `/odom` | Reliable | Teleop, AMCL |
| LaserScan | `/scan` | Reliability **Best Effort** | Teleop, AMCL |
| RobotModel | Description Topic `/robot_description` | Durability **Transient Local** | Teleop, AMCL |
| TF | — | — | AMCL |
| PoseWithCovariance | `/amcl_pose` | Reliable | AMCL |
| ParticleCloud (nav2\_rviz\_plugins) | `/particle_cloud` | Best Effort | AMCL |

- Si el mapa no aparece aunque `/map` existe: Durability en *Volatile*. El map\_server publica el mapa una sola vez y solo lo recibe quien esté en *Transient Local*.
- Si el láser no aparece: Reliability en *Best Effort* (funciona con robot simulado y real; en simulación `/scan` se publica Reliable, así que ahí también va con Reliable, pero con el robot real no).
- La nube de partículas en Humble es `/particle_cloud`, display **ParticleCloud**. No es `PoseArray` ni `/particlecloud`.
- Error «Fixed Frame \[map\] does not exist»: falta la transformada map → odom (sección 6) o AMCL todavía no tiene la pose inicial.

## 4. Mapas (map\_server)

Un mapa son dos ficheros: la imagen (`.png`/`.pgm`, negro = pared, blanco = libre) y un `.yaml` que dice cuánto mide cada píxel y dónde está la esquina.

```yaml
image: rooms.png
mode: trinary
resolution: 0.01
origin: [0.0, 0.0, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.25
```

- **resolution** = metros reales / píxeles. Ejemplo: 5 m en 500 px → 5 / 500 = **0.01** m/px. Ancho de la imagen: `file rooms.png` o `python3 -c "from PIL import Image; print(Image.open('rooms.png').size)"`.
- Plano a escala: metros = mm del papel × escala / 1000; resolución = metros / píxeles. Ejemplo: 594 mm a 1:125 = 74,25 m entre 4678 px ≈ 0.0159.
- **origin** = \[x, y, yaw\] de la esquina **inferior izquierda** de la imagen en el frame `map`. Con \[0, 0, 0\] el mapa va de (0, 0) a (ancho·res, alto·res).
- `image` es relativa al propio `.yaml`.
- En RViz se comprueba en el display Map: Resolution, Width, Height y Position (= origin).

**map\_server.launch.py** (completo; sin el `lifecycle_manager` el mapa no se publica nunca)

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

- La línea `yaml = ...` busca `rooms.yaml` en la carpeta del propio launch, así que funciona lances desde donde lances.

**publish\_map.bash** y **visualize\_map.bash**

```bash
#!/bin/bash
cd "$(dirname "$(readlink -f "$0")")"
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 launch ./map_server.launch.py
```

```bash
#!/bin/bash
cd "$(dirname "$(readlink -f "$0")")"
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
rviz2 -d config_map.rviz
```

- La línea `cd "$(dirname ...)"` hace que el script funcione desde cualquier carpeta. Si no la recuerdas, lanza siempre desde la carpeta del script.
- Al arrancar bien sale «\[lifecycle\_manager\]: Managed nodes are active».
- Comprobar: `ros2 topic echo /map --once --field info` → resolution, width, height y origin.
- config\_map.rviz: Fixed Frame `map`, Grid + Map (Transient Local).

## 5. Modelo de Gazebo (Building Editor)

El modelo se dibuja sobre la misma imagen del mapa, con la misma escala, para que las paredes de Gazebo coincidan con las del mapa.

1. `./launch_tb3_empty_sim.bash` (Gazebo vacío con el robot en (0, 0)).
2. *Edit → Building Editor* (`Ctrl+B`).
3. *File → Import*: elegir la imagen (`rooms.png`) → *Next*.
4. Escala: hacer clic en los dos extremos de una distancia conocida (por ejemplo, el borde exterior) y escribir sus metros (5 m). También vale poner la resolución en *Resolution* (px/m = 1 / resolution = 100).
5. *Wall*: clic en el inicio y doble clic en el final de cada pared, siguiendo las líneas negras. `Esc` corta la pared.
6. *File → Save As*: Name `rooms` y carpeta de destino (por ejemplo `~/.../models`). Crea `rooms/model.config` y `rooms/model.sdf`.
7. *File → Exit Building Editor*.
8. Insertar: pestaña *Insert → Add Path* → la carpeta que **contiene** `rooms/` → clic en `rooms` y colocarlo. Para que quede centrado en (0, 0) se ajusta su pose en el panel izquierdo (*World → Models → rooms → pose*).

Alternativas para insertar:

```bash
export GAZEBO_MODEL_PATH=$PWD/models:$GAZEBO_MODEL_PATH
ros2 launch turtlebot3_gazebo empty_world.launch.py
```

```bash
ros2 run gazebo_ros spawn_entity.py -entity rooms -file models/rooms/model.sdf -x 0 -y 0 -z 0
```

- Con `GAZEBO_MODEL_PATH` exportado antes de lanzar Gazebo, el modelo aparece directamente en *Insert*.
- `model.config` tiene que llevar `<name>rooms</name>`; el Building Editor pone «Untitled» si no le das nombre. El `<model name='...'>` del `.sdf` también.
- El robot debe quedar dentro, en zona libre. Mira el PNG antes de colocar el modelo.
- Entrega: `cd models && zip -r ../rooms.zip rooms` → el zip contiene la carpeta `rooms/` con los dos ficheros.
- Si Gazebo no arranca o da «Service /spawn\_entity unavailable»: `killall gzserver gzclient` y relanzar.

## 6. Transformada map → odom y teleoperación con mapa

La transformada map → odom es dónde cae el origen (0, 0) del mundo de Gazebo, medido en el frame del mapa. En Humble el `/odom` de Gazebo coincide con el mundo de Gazebo (no empieza donde nace el robot), así que la transformada **no depende de `x_pose`/`y_pose`**.

Cadena de frames que RViz necesita:

```text
map → odom → base_footprint → base_link → base_scan
(static_transform_publisher o AMCL) (Gazebo/diff_drive) (robot_state_publisher)
```

**Cálculo de --x --y**

- Mapa de W × H metros con `origin: [ox, oy, 0]` y modelo de Gazebo centrado en (Xm, Ym):
  - x = ox + W/2 − Xm
  - y = oy + H/2 − Ym
- Ejemplo rooms: W = H = 5, origin (0, 0), modelo en (0, 0) → **x = 2.5, y = 2.5** (da igual dónde nazca el robot).
- El robot nacido en (xr, yr) de Gazebo está en (x + xr, y + yr) del mapa. Es lo que debe dar `tf2_echo` y la pose inicial de AMCL.
- Si no cuadra a la primera: teleopera, mira si el láser cae sobre las paredes del mapa y corrige x/y relanzando la transformada.

**Rotación** (si el mapa está girado θ respecto a odom): `qz = sin(θ/2)`, `qw = cos(θ/2)`, qx = qy = 0. 90° → qz = qw = 0.7071; 180° → qz = 1, qw = 0. En Humble también vale `--yaw 1.5708` (radianes) en lugar del cuaternión.

**publish\_transform.bash**

```bash
#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
ros2 run tf2_ros static_transform_publisher --x 2.5 --y 2.5 --z 0 --qx 0 --qy 0 --qz 0 --qw 1 --frame-id map --child-frame-id odom
```

**visualize\_robot.bash**: igual que visualize\_map pero con `rviz2 -d config_robot.rviz`. Config: Fixed Frame `odom` (o `map`), Grid + Map + Odometry + LaserScan + RobotModel.

**Terminales de la práctica Teleoperation**

1. `./launch_tb3_empty_sim.bash` e insertar el modelo
2. `./publish_map.bash`
3. `./publish_transform.bash`
4. `./visualize_robot.bash` → comprobar que el láser encaja con las paredes
5. `ros2 bag record /map /clock /tf /tf_static /robot_description /odom /scan`
6. `ros2 run turtlebot3_teleop teleop_keyboard` → recorrer todas las habitaciones sin chocar
7. `Ctrl+C` en la grabación, `ros2 bag info` y `zip -r`

Comprobar la transformada: `ros2 run tf2_ros tf2_echo map base_footprint` (con el robot quieto recién lanzado debe dar x + xr, y + yr; en rooms con el robot en (0, 0), 2.5, 2.5).

## 7. Localización con AMCL

AMCL sustituye a `publish_map` y `publish_transform`: carga el mapa él mismo y publica map → odom. Si dejas abiertos los otros dos, chocan.

**amcl.launch.py** (lanza nav2 completo con los parámetros del burger; la clave es `params_file`, no `params`)

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

- `map` y `use_sim_time` llegan desde `launch_amcl.bash`; si no los pasas, falla.
- Los parámetros tienen que ser los de `param/humble/burger.yaml`. El `param/burger.yaml` del mismo paquete es de una versión posterior de Nav2 y no vale para Humble.
- Antes del examen comprueba que existe: `ls /opt/ros/humble/share/turtlebot3_navigation2/param/`. Si en ese PC no hay carpeta `humble/` (versión antigua del paquete), ahí `param/burger.yaml` es el de Humble: cambia la ruta a `'param', 'burger.yaml'`.

**launch\_amcl.bash**

```bash
#!/bin/bash
cd "$(dirname "$(readlink -f "$0")")"
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
ros2 launch ./amcl.launch.py use_sim_time:=True map:=$PWD/rooms.yaml
```

- `map:=` con ruta **absoluta** (`$PWD/...`). Una ruta relativa como `../mapa.yaml` falla si lanzas desde otra carpeta.
- `use_sim_time:=True` en simulación (False con robot real).

- Al arrancar sale «\[lifecycle\_manager\_localization\]: Managed nodes are active» y luego muchos «Timed out waiting for transform from base\_link to map» y «Please set the initial pose». Es normal hasta dar la pose inicial; después sale «\[lifecycle\_manager\_navigation\]: Managed nodes are active».

**Pose inicial**: sin ella no hay `map` ni partículas. En RViz, *2D Pose Estimate* → clic en la posición real del robot y arrastrar hacia donde mira (en `empty_world` mira hacia +x, a la derecha). Por terminal, para rooms (robot en 2.5, 2.5):

```bash
ros2 topic pub -w 1 -t 3 /initialpose geometry_msgs/msg/PoseWithCovarianceStamped "{header: {frame_id: map}, pose: {pose: {position: {x: 2.5, y: 2.5}, orientation: {w: 1.0}}}}"
```

- `-t 3` la manda 3 veces. Con `-1` el único mensaje a veces se pierde y AMCL sigue pidiendo la pose.
- Si ha ido bien, en la terminal de AMCL sale «initialPoseReceived» y «Setting pose: 2.500 2.500». Comprobar con `ros2 topic echo /amcl_pose --once`.
- Así la covarianza va a 0 y todas las partículas salen en el mismo punto; vale si la pose es la exacta. Con *2D Pose Estimate* la nube sale repartida.

**config\_amcl.rviz**: Fixed Frame `map`; Grid, RobotModel, TF, LaserScan, Map, PoseWithCovariance (`/amcl_pose`), Odometry y ParticleCloud (`/particle_cloud`). QoS como en la sección 3.

**Terminales de la práctica Localization**

1. `./launch_tb3_empty_sim.bash` e insertar el modelo
2. `./launch_amcl.bash` (esperar a ver «Managed nodes are active»)
3. `./visualize_localization.bash` → *2D Pose Estimate*
4. `ros2 bag record /map /clock /tf /tf_static /robot_description /amcl_pose /particle_cloud /odom /scan`
5. Teleop → la nube se concentra alrededor del robot y la flecha de `/amcl_pose` le sigue
6. `Ctrl+C`, `ros2 bag info` y `zip -r`

## 8. SLAM y navegación

SLAM construye el mapa mientras teleoperas y se guarda con `map_saver_cli`; la navegación usa ese mapa con AMCL y manda al robot a un objetivo.

**Cartographer** (mundo house)

1. `ros2 launch turtlebot3_gazebo turtlebot3_house.launch.py`
2. `ros2 launch turtlebot3_cartographer cartographer.launch.py use_sim_time:=True` (abre su RViz)
3. `ros2 bag record /clock /map /map_updates /odom /robot_description /scan /scan_matched_points2 /submap_list /tf /tf_static`
4. `ros2 run turtlebot3_teleop teleop_keyboard` → recorrer toda la casa despacio
5. Guardar el mapa **sin cerrar Cartographer**: `ros2 run nav2_map_server map_saver_cli -f ~/map` → crea `map.pgm` y `map.yaml`
6. Verificar el bag: `rviz2 -d /opt/ros/humble/share/turtlebot3_cartographer/rviz/tb3_cartographer.rviz` + `ros2 bag play`

**Otros SLAM** (sustituyen al punto 2)

```bash
ros2 launch slam_toolbox online_async_launch.py use_sim_time:=True
ros2 launch rtabmap_demos turtlebot3_scan.launch.py use_sim_time:=True
```

Con slam\_toolbox hay que abrir RViz a mano: Fixed Frame `map`, Map (Transient Local), LaserScan, RobotModel.

**Navegación (Nav2)**

1. `ros2 launch turtlebot3_gazebo turtlebot3_house.launch.py`
2. `ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True map:=$HOME/map.yaml` (abre RViz con Nav2)
3. *2D Pose Estimate* donde está el robot; **no** lanzar `publish_transform` (AMCL ya publica map → odom)
4. *Nav2 Goal* → clic en el destino; o *Waypoint / Nav Through Poses Mode* en el panel Navigation 2 para varios puntos
5. Grabar: `ros2 bag record /clock /tf /tf_static /map /robot_description /scan /odom /amcl_pose /particle_cloud /plan /local_plan /global_costmap/costmap /local_costmap/costmap`
6. Verificar: `rviz2 -d /opt/ros/humble/share/nav2_bringup/rviz/nav2_default_view.rviz` + `ros2 bag play`

- Paquetes (si el examen los pide instalados): `ros-humble-turtlebot3-cartographer`, `ros-humble-slam-toolbox`, `ros-humble-navigation2`, `ros-humble-nav2-bringup`, `ros-humble-turtlebot3-navigation2`.
- Si el robot no se mueve con Nav2 Goal: falta la pose inicial o el objetivo está en zona ocupada o desconocida.

## 9. Sistemas de referencia (teoría)

Un punto del robot pasa al sistema fijo con rotación + traslación; una velocidad solo con la rotación, porque la traslación es constante y se anula al derivar.

Punto: robot (R) → fijo (I), robot en (x, y) con orientación θ:

```latex
{}^{I}P = {}^{I}T_{R}\,{}^{R}P \qquad \begin{bmatrix} x_I \\ y_I \\ 1 \end{bmatrix} = \begin{bmatrix} \cos\theta & -\sin\theta & x \\ \sin\theta & \cos\theta & y \\ 0 & 0 & 1 \end{bmatrix} \begin{bmatrix} x_R \\ y_R \\ 1 \end{bmatrix}
```

Velocidad:

```latex
\begin{bmatrix} \dot{x} \\ \dot{y} \end{bmatrix} = \begin{bmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{bmatrix} \begin{bmatrix} v_x^R \\ v_y^R \end{bmatrix}
```

- Robot diferencial (TurtleBot3): no se mueve de lado, v\_y^R = 0, así que ẋ = v·cosθ y ẏ = v·sinθ; θ̇ = ω.
- Inversa (fijo → robot): se usa la traspuesta de la rotación, R(θ)ᵀ = R(−θ).
- Composición: map→base = (map→odom) · (odom→base). Es lo que hace TF con la cadena de la sección 6.
- Cuaternión ↔ yaw (giro solo en z): qz = sin(θ/2), qw = cos(θ/2); θ = atan2(2(qw·qz + qx·qy), 1 − 2(qy² + qz²)).
- En `/odom`: `pose.pose.position` y `orientation` están en el frame `odom`; `twist.twist.linear.x` (v) y `angular.z` (ω) están en el frame del robot (`base_footprint`).

Comprobación con datos: ẋ medida = Δx/Δt entre dos mensajes de `/odom` debe coincidir con v·cosθ (y lo mismo para y).

## 10. Diagnóstico y errores típicos

Sin internet, el diagnóstico se hace con estos comandos (cada uno en una terminal con la cabecera):

```bash
ros2 topic list
ros2 topic echo /map --once --field info
ros2 topic hz /scan
ros2 topic info -v /scan
ros2 node list
ros2 run tf2_ros tf2_echo map base_footprint
ros2 run tf2_tools view_frames
ros2 bag info rosbag2_...
ros2 pkg list | grep turtlebot3
ros2 launch <paquete> <fichero> --show-args
ros2 run tf2_ros static_transform_publisher --help
```

- `ros2 topic info -v` muestra la QoS de quien publica y de quien se suscribe.
- `view_frames` tarda unos 5 s y genera `frames_AAAA-MM-DD_hh.mm.ss.pdf` (y un `.gv`) en la carpeta actual con el árbol de TF.
- `--show-args` y `--help` sirven para recordar argumentos sin internet.

| Síntoma | Causa | Solución |
| --- | --- | --- |
| `/map` no existe o no se publica | map\_server sin `lifecycle_manager` o ruta del yaml mal | Launch completo (sección 4) y ruta absoluta |
| `/map` existe pero RViz no lo pinta | Durability Volatile | Map → Topic → Durability: Transient Local |
| El láser no aparece | Reliability incompatible o Fixed Frame sin TF | Best Effort; revisar map → odom |
| «Fixed Frame \[map\] does not exist» | Falta la transformada o la pose inicial de AMCL | `publish_transform.bash` o *2D Pose Estimate* |
| Los nodos no se ven entre terminales | Cabecera distinta (`ROS_LOCALHOST_ONLY` / `ROS_DOMAIN_ID`) | Misma cabecera en todas |
| `KeyError: 'TURTLEBOT3_MODEL'` | Falta el export | `export TURTLEBOT3_MODEL=burger` |
| «Service /spawn\_entity unavailable» o Gazebo no abre | gzserver zombi de una ejecución anterior | `killall gzserver gzclient` y relanzar |
| El láser no cuadra con las paredes | x/y de la transformada mal o modelo desplazado | Recalcular (sección 6) y ajustar la pose del modelo |
| AMCL con partículas por todo el mapa | Pose inicial mal o robot movido antes | *2D Pose Estimate* en la posición real, robot quieto |
| Dos mapas o TF que salta; AMCL da «Failed to change state for node: map\_server» | `publish_map`/`publish_transform` abiertos junto a AMCL (dos nodos `map_server`) | Cerrarlos y relanzar AMCL |
| `Permission denied` al lanzar un `.bash` | Sin permiso de ejecución | `chmod +x *.bash` |
| El bag no tiene `metadata.yaml` | Grabación cortada de golpe | Grabar otra vez y parar con `Ctrl+C` |
| Teleop no mueve el robot | La terminal del teleop no tiene el foco o cabecera distinta | Clic en esa terminal; revisar la cabecera |

## 11. Topics a grabar por práctica

En simulación siempre va `/clock`; el enunciado dice qué grabar con palabras, y esta tabla lo traduce a topics.

| Práctica | `ros2 bag record …` |
| --- | --- |
| Teleoperación básica | `/clock /odom /tf /tf_static` |
| Mapa con robot (Teleoperation) | `/map /clock /tf /tf_static /robot_description /odom /scan` |
| Localización AMCL | `/map /clock /tf /tf_static /robot_description /amcl_pose /particle_cloud /odom /scan` |
| SLAM Cartographer | `/clock /map /map_updates /odom /robot_description /scan /scan_matched_points2 /submap_list /tf /tf_static` |
| Navegación Nav2 | `/clock /tf /tf_static /map /robot_description /scan /odom /amcl_pose /particle_cloud /plan /local_plan /global_costmap/costmap /local_costmap/costmap` |

Diccionario enunciado → topic: map → `/map`; clock → `/clock`; transforms → `/tf /tf_static`; robot description → `/robot_description`; odometry → `/odom`; laser → `/scan`; AMCL pose → `/amcl_pose`; particle cloud → `/particle_cloud`.
