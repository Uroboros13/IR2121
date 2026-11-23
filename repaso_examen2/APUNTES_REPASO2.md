# Apuntes examen IR2121 · Simulación, rosbags, SLAM y navegación (ROS 2 Humble)

## 0. Patrón de cualquier ejercicio

Casi todos los ejercicios son combinaciones de las mismas piezas:

| Pieza | Opciones |
| --- | --- |
| **Fuente de datos** | simulación (Gazebo) · bag (`ros2 bag play`) · robot real |
| **Algoritmo** | ninguno (teleop) · map_server · AMCL · SLAM (Cartographer / SLAM Toolbox / RTAB-Map) · Nav2 |
| **Visualización** | RViz con su `.rviz` |
| **Registro** | `ros2 bag record` · `map_saver_cli` |
| **Entrega** | `.rviz`, `.bash`, `.launch.py`, mapas (`.pgm` + `.yaml`), `zip` |

**Orden general**: 1 fuente (Gazebo) → 2 algoritmo (SLAM / Nav2) → 3 RViz → 4 grabación → 5 mover el robot (teleop u objetivos) → 6 parar grabación → 7 guardar / comprimir.

**Una terminal por proceso.** Al acabar: `Ctrl+C` en cada una; si Gazebo se queda colgado: `killall gzserver gzclient` (o `pkill -9 gzserver`).

---

## 1. Cabecera y entorno

```bash
#!/bin/bash
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1
export TURTLEBOT3_MODEL=burger
```

- **Misma cabecera en todas las terminales**: si cambia `ROS_LOCALHOST_ONLY` o `ROS_DOMAIN_ID`, los nodos no se ven.
- Robot real: quitar `ROS_LOCALHOST_ONLY` y poner `export ROS_DOMAIN_ID=N`.
- `TURTLEBOT3_MODEL` = el del enunciado. Hace falta en Gazebo, teleop, Cartographer y Nav2; en el resto no molesta.
- Un `.bash` que pidan = cabecera + el comando. `chmod +x *.bash` → `./script.bash` desde su carpeta.
- Rutas relativas se resuelven desde la carpeta donde se lanza; en `map:=` usar ruta absoluta (`$PWD/mapa.yaml`).
- **Simulación o bag → `use_sim_time:=True`** en todo lo que se lance (SLAM, Nav2, RViz: `rviz2 --ros-args -p use_sim_time:=true`). Robot real → `False` (o no ponerlo).

### Modelos TurtleBot3

| Modelo | Diferencias |
| --- | --- |
| `burger` | pequeño, LDS (láser), sin cámara |
| `waffle` | más ancho, láser + cámara de profundidad |
| `waffle_pi` | más ancho, láser + cámara RGB (`/camera/image_raw`, `/camera/camera_info`) |

Todos publican `/scan`, `/odom`, `/tf`, `/tf_static`, `/imu`, `/joint_states`, `/robot_description`; en simulación además `/clock`. Se mueven con `/cmd_vel`.

---

## 2. Simulación en Gazebo

### 2.1 Lanzar

```bash
ros2 launch turtlebot3_gazebo empty_world.launch.py
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
ros2 launch turtlebot3_gazebo turtlebot3_house.launch.py
ros2 launch turtlebot3_no_GUI.launch.py
```

- Posición inicial: `x_pose:=1.0 y_pose:=2.0` (si el launch los acepta: `--show-args`).
- **`/odom` de Gazebo está en coordenadas del mundo**: con el robot en (x, y) de Gazebo, la odometría arranca en (x, y), no en (0, 0). Por tanto los mapas de SLAM y la pose inicial de AMCL/Nav2 van en esas coordenadas.
- Posiciones por defecto: `empty_world` (0, 0) · `turtlebot3_world` (-2.0, -0.5) · `turtlebot3_house` (-2.0, -0.5).
- `turtlebot3_world`: hexágono con 9 columnas en x, y ∈ {-1.1, 0, 1.1}.

### 2.2 Sin interfaz (GUI)

- Gazebo = `gzserver` (simula) + `gzclient` (ventana). Un launch "no GUI" solo lanza `gzserver`.
- Ver la ventana igualmente: `gzclient` en otra terminal.
- Mensajes normales sin GUI: `Home directory not accessible`, `ALSA…`, `AL lib…` (sin sonido). No afectan.
- Está bien si sale `Successfully spawned entity` y `Advertise odometry on [/odom]`.

### 2.3 Anatomía de un launch de TurtleBot3 (para modificar uno dado)

```python
world = os.path.join(get_package_share_directory('turtlebot3_gazebo'), 'worlds', 'turtlebot3_world.world')
x_pose = LaunchConfiguration('x_pose', default='-2.0')
```

- Cambiar el mundo: el nombre del `.world` (`empty_world.world`, `turtlebot3_world.world`, `turtlebot3_house.world`).
- Cambiar la posición: los `default` de `x_pose`/`y_pose`.
- Partes: `gzserver.launch.py` (mundo) · `gzclient.launch.py` (ventana, quitarlo = sin GUI) · `robot_state_publisher.launch.py` (TF del robot) · `spawn_turtlebot3.launch.py` (robot).
- Ver los mundos disponibles: `ls $(ros2 pkg prefix turtlebot3_gazebo)/share/turtlebot3_gazebo/worlds`

### 2.4 Insertar un modelo propio

```bash
export GAZEBO_MODEL_PATH=$PWD/models:$GAZEBO_MODEL_PATH
ros2 run gazebo_ros spawn_entity.py -entity rooms -file models/rooms/model.sdf -x 0 -y 0 -z 0
```
- O en Gazebo: *Insert → Add Path* → carpeta que contiene el modelo. (Building Editor: ver apuntes del parcial.)

---

## 3. Teleoperación

```bash
ros2 run turtlebot3_teleop teleop_keyboard
```
- `w`/`x` velocidad lineal ± · `a`/`d` angular ± · `s` o espacio: parar. **Mantiene la velocidad al soltar.**
- La terminal del teleop tiene que tener el foco.
- Para SLAM: despacio, girar con el robot casi parado, recorrer todo y **volver a sitios ya vistos** (cierre de bucles).
- Mover sin teclado: `ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.1}, angular: {z: 0.0}}"`

---

## 4. RViz

### 4.1 Crear y guardar una configuración

1. `rviz2` (o `rviz2 -d base.rviz` para partir de otra).
2. **Global Options → Fixed Frame**: `odom` (sin mapa) · `map` (con mapa, SLAM, AMCL, Nav2). Se puede escribir a mano.
3. **Add → By display type** o **By topic**.
4. Ajustar topic y **QoS** de cada display.
5. Vista desde arriba: **Views → Type: TopDownOrtho**.
6. **File → Save Config As → `nombre.rviz`** (Ctrl+S guarda encima).
7. Abrir: `rviz2 -d nombre.rviz`

### 4.2 Catálogo de displays

| Display | Topic | QoS / ajuste |
| --- | --- | --- |
| Grid | — | — |
| TF | — | ver ejes de todos los frames |
| RobotModel | `/robot_description` | Description Source: Topic · Durability Transient Local |
| Odometry | `/odom` | Reliable |
| LaserScan | `/scan` | Reliability **Best Effort** · Size 0.05 · color |
| Image | `/camera/image_raw` | Best Effort (solo waffle_pi) |
| Map (mapa) | `/map` | Durability **Transient Local** |
| Map (global costmap) | `/global_costmap/costmap` | Color Scheme **costmap** |
| Map (local costmap) | `/local_costmap/costmap` | Color Scheme **costmap** |
| Path (ruta global) | `/plan` | — |
| Path (ruta local) | `/local_plan` | — |
| PoseWithCovariance | `/amcl_pose` | Reliable |
| ParticleCloud (nav2_rviz_plugins) | `/particle_cloud` | Best Effort |

- **Herramientas de la barra**: *2D Pose Estimate* → `/initialpose` · *2D Goal Pose* / *Nav2 Goal* → `/goal_pose` · *Publish Point* → `/clicked_point`.
- RViz ya hechos del sistema:
  - Cartographer: `/opt/ros/humble/share/turtlebot3_cartographer/rviz/tb3_cartographer.rviz`
  - Nav2: `/opt/ros/humble/share/nav2_bringup/rviz/nav2_default_view.rviz`
- Si algo no se ve: QoS (Best Effort / Transient Local), Fixed Frame, `use_sim_time`, o el topic no existe (`ros2 topic list`).

---

## 5. Rosbags

### 5.1 Grabar

```bash
ros2 bag record /clock /odom /scan /tf /tf_static
ros2 bag record -o nombre_bag /clock /odom /scan /tf /tf_static
ros2 bag record -a
```
- **Empezar antes de mover el robot.** Parar con `Ctrl+C` **solo al final**; en esa terminal la barra espaciadora **pausa**.
- Sin `-o`: carpeta `rosbag2_AAAA_MM_DD-hh_mm_ss`. Con `-o nombre`: carpeta `nombre` (dentro `metadata.yaml` + `nombre_0.db3`). Si la carpeta ya existe, da error: borrarla o cambiar el nombre.
- `-a` graba todo (muy grande; mejor la lista exacta).
- En simulación **siempre `/clock`**.

### 5.2 Topics según lo que se quiera hacer con el bag

| Para… | Topics |
| --- | --- |
| Ver la trayectoria | `/clock /odom /tf /tf_static` |
| Ver el robot y el láser | + `/robot_description /scan` |
| **Hacer SLAM después** | `/clock /odom /scan /tf /tf_static /robot_description` |
| Mapa + robot | + `/map` |
| AMCL | + `/map /amcl_pose /particle_cloud` |
| SLAM en directo (Cartographer) | `/clock /map /map_updates /odom /robot_description /scan /scan_matched_points2 /submap_list /tf /tf_static` |
| **Navegación** | `/clock /tf /tf_static /map /robot_description /scan /odom /amcl_pose /particle_cloud /plan /local_plan /cmd_vel /global_costmap/costmap /local_costmap/costmap` |
| Cámara | + `/camera/image_raw` |

Diccionario enunciado → topic: clock `/clock` · odometry `/odom` · transforms `/tf /tf_static` · laser/scan `/scan` · robot description `/robot_description` · map `/map` · AMCL pose `/amcl_pose` · particles `/particle_cloud` · path/plan `/plan` · velocity commands `/cmd_vel` · costmaps `/global_costmap/costmap /local_costmap/costmap` · camera `/camera/image_raw` · IMU `/imu`.

### 5.3 Reproducir, comprobar, comprimir

```bash
ros2 bag info nombre_bag
ros2 bag play nombre_bag
ros2 bag play nombre_bag --rate 2
ros2 bag play nombre_bag --topics /scan /odom
zip -r nombre_bag.zip nombre_bag
```
- `ros2 bag info`: **Duration** esperada y todos los topics con mensajes. Si falta `metadata.yaml`, se cortó mal.
- Si el bag ya tiene `/clock` → `play` sin `--clock`. Si no lo tiene y hay nodos con sim time → `play --clock`.
- **Gazebo cerrado al reproducir** (si no, dos `/clock` y dos `/tf`).
- Sin `zip`: `python3 -m zipfile -c nombre.zip nombre_bag/`

---

## 6. Mapas

```yaml
image: map.pgm
mode: trinary
resolution: 0.05
origin: [-5.65, -2.02, 0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.25
```
- `.pgm`/`.png`: blanco libre · negro obstáculo · gris desconocido.
- `resolution`: metros por píxel. `origin`: x, y, yaw de la **esquina inferior izquierda** en el frame `map`. `image`: relativa al `.yaml`.
- Celda ocupada si probabilidad > `occupied_thresh`; libre si < `free_thresh`.

### 6.1 Guardar (map_saver_cli)

```bash
ros2 run nav2_map_server map_saver_cli -f ./map
ros2 run nav2_map_server map_saver_cli -f maps/map_cartographer_1 --ros-args -p use_sim_time:=true
```
- Guarda lo que haya en `/map` en ese momento: el SLAM tiene que seguir abierto.
- Opciones: `-t /otro_topic` · `--fmt png` · `--occ 0.65 --free 0.25` · `--mode trinary|scale|raw`.
- Si se queda esperando: `-p use_sim_time:=true`, `-p map_subscribe_transient_local:=false`, o tener RViz con el Map abierto.
- **Secuencia de N mapas**: repartirlos por la duración (bag de T s → uno cada T/N s; el último al acabar) con nombres numerados (`map_1`… o `map_<alg>_N`).

### 6.2 Publicar un mapa guardado

- Solo el mapa: map_server + lifecycle_manager (launch de los apuntes del parcial) o `ros2 run nav2_map_server map_server --ros-args -p yaml_filename:=$PWD/map.yaml` + activarlo.
- Con localización: AMCL / Nav2 ya cargan el mapa (`map:=`).

---

## 7. SLAM

### 7.1 Dos formas

- **En directo**: Gazebo + SLAM + teleop (+ grabar + guardar mapas mientras).
- **Desde un bag**: Gazebo **cerrado** → **1º SLAM** → **2º `ros2 bag play`** (si se lanza el bag antes, se pierde `/tf_static`) → guardar mapas mientras se reproduce. Repetir el bag para cada algoritmo.

### 7.2 Algoritmos

| Algoritmo | Instalar | Lanzar |
| --- | --- | --- |
| Cartographer | `ros-humble-turtlebot3-cartographer` | `ros2 launch turtlebot3_cartographer cartographer.launch.py use_sim_time:=True` (abre su RViz) |
| SLAM Toolbox | `ros-humble-slam-toolbox` | `ros2 launch slam_toolbox online_async_launch.py use_sim_time:=True` |
| RTAB-Map | `ros-humble-rtabmap-ros` | `ros2 launch rtabmap_demos turtlebot3_scan.launch.py use_sim_time:=True` |

- Todos publican `/map` y la TF `map → odom`.
- SLAM Toolbox y RTAB-Map no abren RViz: abrir uno con Map (`/map`, Transient Local) y Fixed Frame `map`.
- RTAB-Map solo publica `/map` si alguien lo escucha → RViz con Map abierto mientras se guarda.
- Otros modos de SLAM Toolbox: `online_sync_launch.py`, `offline_launch.py`, `localization_launch.py`.
- Ver argumentos: `ros2 launch slam_toolbox online_async_launch.py --show-args`

### 7.3 Teoría

- **SLAM**: con controles y observaciones a lo largo del tiempo, estimar a la vez el estado del robot y el mapa. Todo probabilístico.
- **Cartographer**: *local SLAM* (frontend) inserta cada scan en el submapa actual por scan matching, con el *pose extrapolator* (odometría/IMU) como estimación inicial; los submapas derivan. *Global SLAM* (backend) busca **cierres de bucle** y reordena submapas para un mapa coherente. Filtro paso banda: solo distancias entre min y max.
- **SLAM Toolbox** (Macenski): grafo de poses + scan matching; pensado para entornos dinámicos y mapas grandes.
- **RTAB-Map** (Labbé): grafo con gestión de memoria y detección de bucles; láser y/o visual.

| | Cartographer | SLAM Toolbox | RTAB-Map |
| --- | --- | --- | --- |
| Mapa típico | paredes nítidas, zonas grises | cubre bien, dientes de sierra en libre | el más limpio y completo |
| RViz propio | sí | no | no |

---

## 8. Localización (AMCL)

- AMCL = filtro de partículas: con el mapa, `/scan` y `/odom` estima dónde está el robot y publica `map → odom`, `/amcl_pose` y `/particle_cloud`.
- **No** lanzar a la vez `publish_map` / `static_transform_publisher map→odom`: chocan.
- Pose inicial obligatoria (ver 9.3). Al moverse, la nube se concentra alrededor del robot.
- Parámetros de TurtleBot3: `/opt/ros/humble/share/turtlebot3_navigation2/param/` (`humble/<modelo>.yaml` si existe la carpeta; si no, `<modelo>.yaml`). Comprobar con `ls`.
- Detalle (launch, transformada manual): apuntes del parcial.

---

## 9. Navegación (Nav2)

### 9.1 Piezas

`map_server` (mapa) + `amcl` (localización) + **planner** (ruta global `/plan`) + **controller** (ruta local `/local_plan`, publica `/cmd_vel`) + **costmaps** + **bt_navigator** (coordina) + `lifecycle_manager` (activa nodos).

- **Costmap global**: todo el mapa, para planificar. **Local**: alrededor del robot, con el láser, para esquivar.
- Capas: *static* (del mapa) · *obstacle* (del láser) · *inflation* (margen de seguridad alrededor de obstáculos).

### 9.2 Lanzar

```bash
ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True map:=$PWD/maps/map.yaml
```
- Abre RViz con `nav2_default_view`. Argumentos: `--show-args` (`map`, `params_file`, `use_sim_time`).
- Sin su RViz: `ros2 launch nav2_bringup bringup_launch.py use_sim_time:=True map:=$PWD/map.yaml params_file:=<ruta>/<modelo>.yaml`
- Espera a "Managed nodes are active". Antes de la pose inicial salen avisos de TF ("Please set the initial pose"): normal.

### 9.3 Pose inicial

- RViz: **2D Pose Estimate** → clic donde está el robot y arrastrar hacia donde mira.
- Terminal:
```bash
ros2 topic pub -t 3 -r 2 /initialpose geometry_msgs/msg/PoseWithCovarianceStamped "{header: {frame_id: map}, pose: {pose: {position: {x: -2.0, y: -0.5}, orientation: {w: 1.0}}}}"
```
- Coordenadas = posición del robot en Gazebo si el mapa salió de un SLAM en esa simulación (odom = mundo). Ej. `turtlebot3_world`: (-2.0, -0.5).
- `-t 3`: 3 veces, por si AMCL aún no escuchaba. Comprobar: `ros2 topic echo /amcl_pose --once`.

### 9.4 Objetivos

- RViz: **2D Goal Pose** / **Nav2 Goal** → clic + arrastrar orientación. Varios seguidos: panel Navigation 2 → *Waypoint / Nav Through Poses Mode*.
- Terminal (espera a que acabe):
```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "{pose: {header: {frame_id: map}, pose: {position: {x: 0.55, y: 0.55}, orientation: {w: 1.0}}}}"
```
- O publicar en `/goal_pose` (`geometry_msgs/msg/PoseStamped`, frame `map`).
- Objetivos en zona **libre** del mapa, lejos de paredes (el costmap infla los obstáculos).
- Orientación (yaw θ): `z = sin(θ/2)`, `w = cos(θ/2)` → 0°: `{w: 1}` · 90°: `{z: 0.707, w: 0.707}` · 180°: `{z: 1, w: 0}` · -90°: `{z: -0.707, w: 0.707}`.
- Ver acciones: `ros2 action list` · `ros2 action info /navigate_to_pose` · `ros2 interface show nav2_msgs/action/NavigateToPose`.

### 9.5 Grabar y comprobar

- Grabar **antes** de mandar objetivos (topics en 5.2).
- Comprobar: `rviz2 -d /opt/ros/humble/share/nav2_bringup/rviz/nav2_default_view.rviz` + `ros2 bag play`.

---

## 10. Ejercicio tipo (repaso): pasos completos

**Teleoperation and recording** → entregar `config_teleop.rviz` + `rosbag_teleop.zip`
1. T1 `ros2 launch turtlebot3_no_GUI.launch.py` (con `TURTLEBOT3_MODEL=waffle_pi`).
2. T2 `rviz2` → Odometry, LaserScan, RobotModel, Image, TF · Fixed Frame `odom` → guardar `config_teleop.rviz`.
3. T3 `ros2 bag record -o rosbag_teleop /clock /odom /scan /tf /tf_static /robot_description`
4. T4 teleop 3–5 min → `Ctrl+C` en T3 → `ros2 bag info` → `zip -r rosbag_teleop.zip rosbag_teleop`

**SLAM** → entregar `config_slam.rviz` + `maps.zip`
1. RViz anterior + Map (`/map`) · Fixed Frame `map` → guardar `config_slam.rviz`.
2. Gazebo cerrado. Por cada algoritmo: lanzarlo → `ros2 bag play rosbag_teleop` → 5 × `map_saver_cli -f maps/map_<alg>_N` repartidos → `Ctrl+C`.
3. Nombres: `map_slam_toolbox_N`, `map_cartographer_N`, `map_rtabmap_N` → `zip -r maps.zip maps`

**Navigation** → entregar `nav2_view.rviz` + `rosbag_nav.zip`
1. Gazebo recién lanzado + `navigation2.launch.py … map:=<mejor mapa>`.
2. RViz: Map + global costmap + local costmap + Path (+ robot, láser, TF) → guardar `nav2_view.rviz`.
3. Pose inicial (-2.0, -0.5) → `ros2 bag record -o rosbag_nav …` → 5 objetivos → `Ctrl+C` → `zip -r rosbag_nav.zip rosbag_nav`

---

## 11. Diagnóstico sin internet

```bash
ros2 topic list
ros2 topic info -v /scan
ros2 topic hz /scan
ros2 topic echo /odom --once
ros2 topic echo /map --once --field info
ros2 node list
ros2 param list /amcl
ros2 run tf2_ros tf2_echo map base_footprint
ros2 run tf2_tools view_frames
ros2 bag info carpeta_bag
ros2 pkg prefix nombre_paquete
ls $(ros2 pkg prefix nombre_paquete)/share/nombre_paquete/launch
ros2 launch paquete fichero.launch.py --show-args
ros2 interface show geometry_msgs/msg/PoseWithCovarianceStamped
```
- `topic info -v`: QoS de publicadores y suscriptores. `view_frames`: PDF con el árbol de TF.
- Árbol de TF esperado: `map → odom → base_footprint → base_link → base_scan` (map→odom: SLAM, AMCL o transformada estática; odom→base_footprint: Gazebo/diff drive; resto: robot_state_publisher).

## 12. Problemas típicos

| Problema | Solución |
| --- | --- |
| Terminales que no se ven | misma cabecera (`ROS_LOCALHOST_ONLY` / `ROS_DOMAIN_ID`) |
| `KeyError: TURTLEBOT3_MODEL` / no aparece el robot | `export TURTLEBOT3_MODEL=…` |
| Gazebo no arranca, "/spawn_entity unavailable" | `killall gzserver gzclient` y relanzar |
| LaserScan / Image no se ven | QoS **Best Effort** |
| Mapa no aparece en RViz | Durability **Transient Local** |
| "Fixed Frame [map] does not exist" | falta SLAM / AMCL / transformada, o falta la pose inicial |
| "No transform from…" | Fixed Frame mal o falta `use_sim_time` |
| SLAM no hace nada con el bag | falta `use_sim_time:=True` o se lanzó después del bag |
| Saltos raros al reproducir | Gazebo sigue abierto |
| `map_saver_cli` no guarda | `use_sim_time`, `map_subscribe_transient_local:=false`, RViz con Map abierto |
| La grabación dura segundos | se pulsó `Ctrl+C` o espacio en su terminal |
| El bag no tiene `metadata.yaml` | se cortó de golpe: grabar otra vez |
| Error "already exists" al grabar | borrar la carpeta del bag o usar otro `-o` |
| AMCL con partículas por todo el mapa | pose inicial mal o robot movido antes |
| Nav2 no se mueve | falta la pose inicial, u objetivo en zona ocupada/desconocida |
| Dos `map_server` / TF que salta | cerrar `publish_map`/transformada si hay AMCL o Nav2 |
| `Permission denied` al lanzar `.bash` | `chmod +x *.bash` |
| Teleop no mueve el robot | la terminal del teleop sin foco |
