# Plan completo: modelo TD_n1 + Localización (AMCL) en simulación

Todo en una sola sesión de Docker. Coloca estos scripts en la carpeta raíz de tu
repo `IR2121` (al mismo nivel que la carpeta `Worlds/`).

---

## 0. Preparar Docker (una sola vez)

```bash
docker rm contenedor_ros2 cranky_albattani   # limpia los contenedores viejos (opcional)

pip install --user rocker
export PATH="$HOME/.local/bin:$PATH"
```

## 1. Crear el contenedor (cada sesión nueva) o reanudar el existente

Primera vez:
```bash
rocker --x11 --home --user --network host --privileged \
  osrf/ros:humble-desktop bash
```
`--home` monta tu carpeta personal real: los archivos que edites o crees se
guardan en tu disco de verdad, no se pierden al salir.

Siguientes veces (reanudar el mismo contenedor):
```bash
docker ps -a                     # busca el NAME que le puso rocker
docker start -ai <ese_nombre>
```

## 2. Dentro del contenedor, instalar lo que falte (solo la primera vez)

```bash
sudo apt update
sudo apt install -y \
    ros-humble-gazebo-ros-pkgs \
    ros-humble-turtlebot3 \
    ros-humble-turtlebot3-msgs \
    ros-humble-turtlebot3-simulations \
    ros-humble-turtlebot3-navigation2
```

---

## 3. Construir el modelo TD_n1 (homework del Building Editor)

```bash
cd ~/IR2121
./Worlds/scripts/launch_tb3_empty_sim.bash
```

En Gazebo:
1. `Edit > Building Editor`
2. `File > Import` → selecciona `Worlds/TD_n1.png` como plano de fondo
3. Traza las paredes de **TD1107AL** y **TD1118CP** (aprobado). Si quieres el
   excelente, añade también **TD2116CP**.
4. `File > Save As` → guarda el modelo como `TD_n1` dentro de
   `Worlds/models/TD_n1/` (debe generar `model.sdf` + `model.config`)
5. Sal del editor. Panel **Insert** → `Add Path` a `Worlds/models/TD_n1/` →
   insértalo en el mundo, cerca del robot.

**Entregable del homework:**
```bash
cd ~/IR2121/Worlds/models
zip -r TD_n1.zip TD_n1/
```

---

## 4. Task 1 de Localización (AMCL) — enlaza directo, mismo mundo ya abierto

Abre terminales nuevas (todas dentro del mismo contenedor: `docker exec -it <nombre> bash`
si quieres una terminal extra sin cerrar la que tiene Gazebo abierto).

**Terminal A — empieza grabando ANTES que nada más** (por si luego faltan topics al reproducir):
```bash
mkdir -p ~/bags_localizacion && cd ~/bags_localizacion
~/IR2121/record_bag_sim.bash
```

**Terminal B — AMCL:**
```bash
cd ~/IR2121
./launch_amcl_sim.bash
```
*(AMCL lanza su propio `map_server` y calcula él mismo la transformación
`map → odom` — no necesitas `publish_map.bash` ni `publish_transform.bash`,
esos son de la tarea anterior sin AMCL.)*

**Terminal C — RViz:**
```bash
cd ~/IR2121/Worlds/scripts
./visualize_localization.bash
```
En RViz, usa la herramienta **2D Pose Estimate** para marcar dónde está
realmente el robot en el mapa.

**Terminal D — teleoperar:**
```bash
cd ~/IR2121
./teleop_sim.bash
```
Conduce por el edificio; verás la nube de partículas converger alrededor de
la pose real.

Tras **60-90 segundos** de movimiento: `Ctrl+C` en la **Terminal A** para parar
la grabación. Cierra Gazebo, RViz y AMCL.

---

## 5. Verificación antes de entregar

```bash
cd ~/IR2121/Worlds/scripts
./visualize_localization.bash
```
En otra terminal:
```bash
cd ~/bags_localizacion
~/IR2121/play_bag.bash rosbag2_XXXX/
```
Confirma en RViz que se ven: mapa, odometría, láser, pose AMCL (con
covarianza) y la nube de partículas. Haz la captura de pantalla aquí.

```bash
cd ~/bags_localizacion
zip -r rosbag2_localizacion.zip rosbag2_XXXX/
```

---

## Entregables finales

| Tarea | Archivos |
|---|---|
| Homework modelo | `TD_n1.zip` |
| Task 1 Localización | `rosbag2_localizacion.zip` + captura de RViz |

## Scripts incluidos en este paquete

- `teleop_sim.bash` / `teleop_robot.bash`
- `launch_amcl_sim.bash` / `launch_amcl_robot.bash`
- `record_bag_sim.bash` / `record_bag_robot.bash`
- `play_bag.bash` / `verify_bag.bash`

Los de `Worlds/scripts/` (`launch_tb3_empty_sim.bash`, `visualize_localization.bash`,
`amcl.launch.py`, `config_amcl.rviz`) ya los tienes correctos del paquete oficial
del curso — no hace falta tocarlos.
