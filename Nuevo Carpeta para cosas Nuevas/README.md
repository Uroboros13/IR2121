# Plan completo: modelo TD_n1 + Localización (AMCL) en simulación y con robot real

Todo se ejecuta dentro del contenedor Docker `ir2121_humble` (ROS 2 Humble +
Gazebo 11). La carpeta base de estos scripts es:

```bash
B="$HOME/Documentos/GitHub/IR2121/Nuevo Carpeta para cosas Nuevas"
```

(en los comandos de abajo, `$B` es esa carpeta; defínela en cada terminal o usa la ruta completa)

---

## 0. Antes de nada (cada vez que reinicies el portátil)

En el host:
```bash
xhost +local:docker
```

## 1. Entrar al contenedor

```bash
docker start -ai ir2121_humble          # si está parado
docker exec -it ir2121_humble bash      # para abrir terminales extra
```
No uses `docker run` otra vez: crearía un contenedor nuevo sin los paquetes instalados.

## 2. Dentro del contenedor, instalar lo que falte (solo la primera vez)

```bash
apt update
apt install -y \
    ros-humble-gazebo-ros-pkgs \
    ros-humble-turtlebot3 \
    ros-humble-turtlebot3-msgs \
    ros-humble-turtlebot3-simulations \
    ros-humble-turtlebot3-navigation2
```

---

## 3. Homework: modelo del edificio TD, nivel 1

Requisitos: **TD1107AL + TD1118CP** (aprobado), **+ TD2116CP** (excelente).
Entregar `TD_n1.yaml`, `TD_n1.zip` (con `model.config` y `model.sdf`) y un bag
teleoperando por el edificio.

### Medidas reales (plano TD-02, A1, escala 1/200)

`TD_n1.png` = 6623 × 4678 px → **0.0254 m/px** (= **39.37 px/m**).
En Gazebo **Z es la altura**; X e Y son el suelo (X = horizontal del plano,
Y = vertical del plano).

| Medida | Eje Gazebo | Metros |
|---|---|---|
| Fachada exterior ala izquierda → fachada exterior ala derecha | X | **≈ 117.9** |
| Lo mismo incluyendo los dos cuerpos de entrada laterales | X | ≈ 137.9 |
| Alas laterales, de arriba a abajo | Y | **≈ 88.8** |
| Imagen completa (`TD_n1.png`) | X × Y | 168.22 × 118.82 |

Comprobación: el aula TD1104AA mide ~11.1 m de ancho interior; con sus
109.88 m² del plano sale ~9.9 m de fondo, coherente con la escala.

### Pasos en el Building Editor

```bash
cd "$B/Worlds/scripts"
./launch_tb3_empty_sim.bash
```
1. `Edit > Building Editor` (Ctrl+B).
2. Botón **Import** (panel izquierdo) → elige `Worlds/TD_n1.png` →
   **Resolution: 39.37 px/m** (o traza una línea sobre la fachada larga
   de las alas y escribe 117.9 m).
3. Dibuja con **Wall** sobre el plano: TD1107AL, TD1118CP (y TD2116CP).
   Doble clic en una pared para ajustar grosor (0.15 m por defecto) y altura.
   Deja huecos en las puertas para que pase el robot (burger ≈ 0.14 m de radio).
4. `File > Save As` → nombre **TD_n1**, ubicación `$B/Worlds/models/`
   (se crea `Worlds/models/TD_n1/` con `model.config` + `model.sdf`).
5. `File > Exit Building Editor`. Panel **Insert** → `Add Path` →
   `Worlds/models` → arrastra **TD_n1** al mundo.
6. Mueve el robot dentro del edificio: panel **World > Models > burger > pose**.

### Corregir la escala del modelo

```bash
cd "$B" && ./escalar_modelo.py 1.16
```
- La primera vez renombra `Worlds/models/TD_n1` → `TD_n1_original`.
- Siempre genera `Worlds/models/TD_n1` a partir de `TD_n1_original`, así que
  el factor no se acumula: `./escalar_modelo.py 1.2` es 1.2 × el original.
- Escala posiciones y longitudes de pared en X e Y; el grosor (0.15 m) y la
  altura (2.5 m) se mantienen salvo `--escalar-grosor` / `--escalar-altura`.
- Después: cierra Gazebo, vuelve a abrirlo e inserta de nuevo **TD_n1**.

### Mapa (`TD_n1.yaml`)

`resolution: 0.0254` ya está bien. El `origin` actual (`[-41.5,-28, 0]`) es el
del TI: cámbialo. Opción sencilla: centrar la imagen en el origen del mapa:
```yaml
origin: [-84.11, -59.41, 0]
```
Opcional (paso 4 de las diapositivas de mapas): limpiar textos y puertas de
`TD_n1.png` con GIMP para que el láser case mejor.

### Alinear mapa y Gazebo, y grabar el bag del homework

**Terminal A — grabar primero:**
```bash
mkdir -p ~/bags_homework && cd ~/bags_homework
"$B"/record_bag_homework.bash        # /clock /map /odom /scan /tf /tf_static
```
**Terminal B — Gazebo** (si no estaba abierto) con el modelo insertado.

**Terminal C — mapa TD:** `cd "$B" && ./publish_map_td.bash`

**Terminal D — transformada map→odom:** `cd "$B" && ./publish_transform_td.bash X Y [YAW]`

**Terminal E — RViz:** `cd "$B/Worlds/scripts" && ./visualize_robot.bash`

**Terminal F — teleop:** `cd "$B" && ./teleop_sim.bash`

Ajuste de X, Y: empieza con `0 0`. Si el láser (rojo) no cae sobre las paredes
del mapa:
1. Usa **Publish Point** en RViz y haz clic en el sitio del plano donde el
   robot está de verdad en Gazebo. Lee el punto con
   `ros2 topic echo /clicked_point` → (Px, Py).
2. Lee la odometría del robot: `ros2 topic echo --once /odom --no-arr`
   → `pose.pose.position` (Ox, Oy).
3. Relanza la Terminal D con `X = Px - Ox` y `Y = Py - Oy`.

Si el mapa está **girado 90°** respecto a Gazebo, pasa YAW en radianes
(`1.5708` = +90°, `-1.5708` = -90°, `3.1416` = 180°). Con giro, X e Y cambian:

| YAW | X | Y |
|---|---|---|
| `1.5708` | `Px + Oy` | `Py - Ox` |
| `-1.5708` | `Px - Oy` | `Py + Ox` |
| `3.1416` | `Px + Ox` | `Py + Oy` |

Si con `1.5708` el láser queda girado al revés, usa `-1.5708`.
En la Task 1 (AMCL) esto no hace falta: **2D Pose Estimate** ya corrige el giro.
Cuando encaje, para la grabación y vuelve a empezar desde la Terminal A.

**Entregables del homework:**
```bash
cd "$B/Worlds/models" && zip -r TD_n1.zip TD_n1/
cd ~/bags_homework && zip -r rosbag2_homework.zip rosbag2_XXXX/
```
más `Worlds/TD_n1.yaml`.

---

## 4. Task 1 de Localización (AMCL) — enlaza directo, mismo mundo ya abierto

Abre terminales nuevas (todas dentro del mismo contenedor: `docker exec -it ir2121_humble bash`
si quieres una terminal extra sin cerrar la que tiene Gazebo abierto).

**Terminal A — empieza grabando ANTES que nada más** (por si luego faltan topics al reproducir):
```bash
mkdir -p ~/bags_localizacion && cd ~/bags_localizacion
"$B"/record_bag_sim.bash
```

**Terminal B — AMCL:**
```bash
cd "$B"
./launch_amcl_sim.bash
```
*(AMCL lanza su propio `map_server` y calcula él mismo la transformación
`map → odom` — no necesitas `publish_map.bash` ni `publish_transform.bash`,
esos son de la tarea anterior sin AMCL.)*

**Terminal C — RViz:**
```bash
cd "$B/Worlds/scripts"
./visualize_localization.bash
```
En RViz, usa la herramienta **2D Pose Estimate** para marcar dónde está
realmente el robot en el mapa.

**Terminal D — teleoperar:**
```bash
cd "$B"
./teleop_sim.bash
```
Conduce por el edificio; verás la nube de partículas converger alrededor de
la pose real.

Tras **60-90 segundos** de movimiento: `Ctrl+C` en la **Terminal A** para parar
la grabación. Cierra Gazebo, RViz y AMCL.

---

## 5. Verificación antes de entregar

```bash
cd "$B/Worlds/scripts"
./visualize_localization.bash
```
En otra terminal:
```bash
cd ~/bags_localizacion
"$B"/play_bag.bash rosbag2_XXXX/
```
Confirma en RViz que se ven: mapa, odometría, láser, pose AMCL (con
covarianza) y la nube de partículas. Haz la captura de pantalla aquí.

```bash
cd ~/bags_localizacion
zip -r rosbag2_localizacion.zip rosbag2_XXXX/
```

---

---

## 6. Task 2: localización con el TurtleBot 3 real (laboratorio)

Requisitos del PDF: **no** definir `ROS_LOCALHOST_ONLY` y **sí** definir
`ROS_DOMAIN_ID` igual al del robot. Los scripts `*_robot.bash` hacen ambas
cosas: reciben el `ROS_DOMAIN_ID` como primer argumento y quitan
`ROS_LOCALHOST_ONLY` aunque lo tengas exportado.

Conexión: PC del laboratorio (WiFi PIROBOTNET6), portátil del laboratorio, o
tu portátil con dongle WiFi USB / cable Ethernet. Con este contenedor
(`--network host`) el portátil sirve igual.

**Terminal 1 — robot (ssh):**
```bash
ssh ubuntu@192.168.0.XXX        # contraseña: turtlebot
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=burger      # waffle_pi en los robots 111-112
export LDS_MODEL=LDS-01             # LDS-02 en los robots 202-206
export ROS_DOMAIN_ID=N
ros2 launch turtlebot3_bringup robot.launch.py
```

| Robots | TURTLEBOT3_MODEL | LDS_MODEL | ROS_DOMAIN_ID |
|---|---|---|---|
| 101-110 | burger | LDS-01 | 1, 2, 3, 4… según el robot |
| 111-112 | waffle_pi | LDS-01 | 11 o 12 |
| 202-206 | burger | LDS-02 | 22, 23, 24, 25, 26 |

**Terminal 2 — comprobar que llegan los datos** (`/odom` sin arrays, `/scan` con best effort):
```bash
cd "$B" && ./check_robot.bash N
```

**Terminal 3 — grabar PRIMERO** (antes que AMCL y RViz):
```bash
mkdir -p ~/bags_robot && cd ~/bags_robot
"$B"/record_bag_robot.bash N
```

**Terminal 4 — AMCL** (sin `use_sim_time`, mapa `Worlds/TD_n1.yaml`):
```bash
cd "$B" && ./launch_amcl_robot.bash N
```

**Terminal 5 — RViz:**
```bash
cd "$B" && ./visualize_localization_robot.bash N
```
Usa **2D Pose Estimate** para marcar dónde está el robot en el mapa.

**Terminal 6 — teleoperar:**
```bash
cd "$B" && ./teleop_robot.bash N
```
Si es un waffle_pi: `TURTLEBOT3_MODEL=waffle_pi ./teleop_robot.bash N`.

Graba **entre 1 y 3 minutos** y para con `Ctrl+C` en la Terminal 3.
Verifica como en el apartado 5, pero con `./visualize_localization_robot.bash N`.

Apagado del robot: `Ctrl+C` en el bringup → `sudo halt -p` → espera a que el
LED amarillo deje de parpadear → apaga → batería al cargador.

---

## 7. Task 2 (variante): localización con el TurtleBot 2 real

Igual que el apartado 6, salvo dos cosas:

1. **Bringup**: sigue las instrucciones del enlace "TurtleBot 2 physical robot"
   del PDF (página 160); es un documento del profesor que no está en el PDF.
2. **Teleoperación**: el teleop del TurtleBot 3 no sirve; usa
   ```bash
   cd "$B" && ./teleop_tb2.bash N                       # publica en /cmd_vel
   cd "$B" && ./teleop_tb2.bash N /commands/velocity    # si el robot escucha en otro topic
   ```
   Comprueba el topic real con `ros2 topic list` tras el bringup.

AMCL, RViz, grabación y verificación: los mismos scripts `*_robot.bash`.

---

## Entregables finales

| Tarea | Archivos |
|---|---|
| Homework modelo | `TD_n1.yaml` + `TD_n1.zip` (modelo Gazebo) + `rosbag2_….zip` |
| Task 1 Localización (sim) | `rosbag2_localizacion.zip` + captura de RViz |
| Task 2 Localización (robot real) | `rosbag2_….zip` (1-3 min) |

## Scripts incluidos en este paquete

- Homework: `publish_map_td.bash`, `publish_transform_td.bash X Y [YAW]`, `record_bag_homework.bash`
- Simulación: `teleop_sim.bash`, `launch_amcl_sim.bash`, `record_bag_sim.bash`, `visualize_localization.bash`
- Robot real (argumento: `ROS_DOMAIN_ID`): `check_robot.bash`, `launch_amcl_robot.bash`,
  `record_bag_robot.bash`, `visualize_localization_robot.bash`, `teleop_robot.bash`, `teleop_tb2.bash`
- Comunes: `play_bag.bash`, `verify_bag.bash`

`Worlds/scripts/config_amcl.rviz` está corregido: la nube de partículas se
muestra con `nav2_rviz_plugins/ParticleCloud` en `/particle_cloud` (el topic
que publica AMCL en Humble), como en la diapositiva del curso.
