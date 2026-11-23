# Prácticas Maps / Simulation / Teleoperation / Localization (ROS 2 Humble en Docker)

Todo se ejecuta desde la carpeta `04_repaso_parcial/trabajo` dentro del contenedor `ir2121_humble`.
Cada script hace `cd` a su propia carpeta, así que da igual desde dónde lo lances.

## Entrar al contenedor (en cada terminal)

En cada terminal nueva del portátil:

    xhost +local:docker
    docker start ir2121_humble
    docker exec -it ir2121_humble bash
    cd ~/Documentos/GitHub/IR2121/04_repaso_parcial/trabajo

(`docker start` no hace nada si el contenedor ya está en marcha. Dentro del contenedor `~` es `/home/ulisses`.)

Solo si faltara algo, dentro del contenedor:

    apt update
    apt install -y ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-turtlebot3-navigation2 ros-humble-turtlebot3-simulations ros-humble-turtlebot3-teleop ros-humble-gazebo-ros-pkgs
    chmod +x *.bash

## 1. Maps

| Terminal | Comando |
|---|---|
| 1 | `./publish_map.bash` |
| 2 | `./visualize_map.bash` |

Debe verse el mapa de 5 x 5 m (Resolution 0.01, Width 500, Height 500, origen 0, 0).

## 2. Simulation

| Terminal | Comando |
|---|---|
| 1 | `./launch_tb3_empty_sim.bash` |
| 2 | `./insert_rooms.bash` |

También puedes insertarlo a mano: pestaña **Insert** de Gazebo → aparece `rooms` (el script añade `models/` a `GAZEBO_MODEL_PATH`) → colócalo en (0, 0).
El robot aparece en el centro de las habitaciones. Entrega: `rooms.zip`.

## 3. Teleoperation (grabar rosbag_teleop)

| Terminal | Comando |
|---|---|
| 1 | `./launch_tb3_empty_sim.bash` (espera a ver el robot en Gazebo) |
| 2 | `./insert_rooms.bash` |
| 3 | `./publish_map.bash` |
| 4 | `./publish_transform.bash` |
| 5 | `./visualize_robot.bash` (el láser verde debe caer sobre las paredes del mapa) |
| 6 | `./record_teleop.bash` |
| 7 | `./teleop.bash` |

Con la terminal 7 seleccionada: `w`/`x` suben/bajan la velocidad lineal, `a`/`d` la angular, `s` o espacio paran.
Recorre las cuatro habitaciones sin chocar, despacio (velocidad lineal ≤ 0.15), unos 3-5 minutos. Vuelve a parar el robot (`s`) antes de terminar.

Para parar: `Ctrl+C` primero en la terminal 6 (grabación), luego en las demás (7, 5, 4, 3, 1).

Comprobar el bag (en el contenedor):

    ./check_bag.bash rosbag_teleop_*

Los 7 topics (/map /clock /tf /tf_static /robot_description /odom /scan) deben tener `Count` > 0 y al final debe salir `MOVIMIENTO OK`.

Comprimir y copiar (en una terminal del portátil, fuera del contenedor):

    cd ~/Documentos/GitHub/IR2121/04_repaso_parcial/trabajo
    rm -f rosbag_teleop.zip
    zip -r rosbag_teleop.zip rosbag_teleop_*/
    cp rosbag_teleop.zip ../entrega/3_Teleoperation/

## 4. Localization (grabar rosbag_amcl)

Cierra todo lo anterior, sobre todo `publish_map` y `publish_transform`: AMCL publica él mismo el mapa y la transformada map → odom. Relanza la simulación para que el robot vuelva al centro (2.5, 2.5 del mapa).

| Terminal | Comando |
|---|---|
| 1 | `./launch_tb3_empty_sim.bash` |
| 2 | `./insert_rooms.bash` |
| 3 | `./visualize_localization.bash` (ábrelo ANTES que AMCL; al principio no sale el mapa, es normal) |
| 4 | `./launch_amcl.bash` (espera unos 15 s: envía la pose inicial 2.5, 2.5 a los 10 s) |
| 5 | `./record_localization.bash` |
| 6 | `./teleop.bash` |

AMCL solo publica `/particle_cloud` cuando recibe una pose inicial o cuando el robot se mueve, y RViz no recibe los mensajes anteriores a su arranque. Por eso RViz va antes que AMCL.
No muevas el robot hasta que AMCL tenga la pose inicial (flecha de /amcl_pose y nube roja de partículas sobre el robot en RViz). Si no aparecen, pulsa **2D Pose Estimate** en RViz y haz clic en el robot arrastrando hacia la derecha (eje x).
Recorre las habitaciones sin chocar, despacio, unos 3-5 minutos; las partículas deben concentrarse sobre el robot.

Para parar: `Ctrl+C` primero en la terminal 5 (grabación), luego en las demás.

    ./check_bag.bash rosbag_amcl_*

Los 9 topics (los 7 de antes más /amcl_pose y /particle_cloud) con `Count` > 0 y `MOVIMIENTO OK`.

    cd ~/Documentos/GitHub/IR2121/04_repaso_parcial/trabajo
    rm -f rosbag_amcl.zip
    zip -r rosbag_amcl.zip rosbag_amcl_*/
    cp rosbag_amcl.zip ../entrega/4_Localization/

## Si hay que repetir una grabación

Borra el intento fallido dentro del contenedor (los bags los crea root): `rm -rf rosbag_teleop_*` o `rm -rf rosbag_amcl_*`, así el `zip` solo coge el bueno.

## Revisar un bag reproduciéndolo

    ./play_bag.bash rosbag_amcl_XXXX

En otra terminal, `./visualize_localization.bash` (o `./visualize_robot.bash` para el de teleoperación).

## Datos del mapa y del modelo

- `rooms.png`: 500 x 500 px para 5 x 5 m → resolución 0.01 m/px, origen (0, 0).
- Modelo `rooms`: centrado en el origen de Gazebo, paredes de 5 cm medidas sobre el propio PNG.
- El robot nace en (0, 0) de Gazebo = (2.5, 2.5) del mapa → `publish_transform.bash` publica map → odom con x = 2.5, y = 2.5.
- Ojo con el tabique corto de abajo en el centro (x ≈ 2.55 m del mapa, de y = 0 a 0.8 m): sobresale de la pared inferior.
