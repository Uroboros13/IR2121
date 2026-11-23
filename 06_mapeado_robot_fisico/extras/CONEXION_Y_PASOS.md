# Mapping con el robot físico desde el portátil (Ubuntu 24.04) por cable

El robot lleva ROS 2 Humble y tu portátil Jazzy. Dos distribuciones distintas no tienen garantizado entenderse, así que **todo lo de ROS se ejecuta dentro del Docker `ir2121_humble`**. Lanzado con `--network host`, el contenedor usa directamente el cable Ethernet del portátil.

Cosas que necesitas: cable Ethernet (y adaptador USB-Ethernet si el portátil no tiene puerto), robot cargado y encendido, y un minuto en un PC del laboratorio para averiguar la IP de cable del robot.

## 1. Configurar el cable del portátil como «Link-local» (una sola vez)

Nombre de tu interfaz de cable (empieza por `en`, por ejemplo `enp3s0` o `enx...` si es un adaptador USB):

```bash
ip -br link
```

Crear la conexión (cambia `enp3s0` por la tuya):

```bash
nmcli con add type ethernet ifname enp3s0 con-name robot-cable ipv4.method link-local ipv6.method disabled
```

También vale por la interfaz gráfica: *Configuración → Red → Cableada → ⚙ → IPv4 → Solo enlace local (Link-Local Only)*.

## 2. Averiguar la IP de cable del robot

Desde un PC del laboratorio (WiFi PIROBOTNET6), con la IP WiFi del robot (`192.168.0.1xx`, la del robot que te toque):

```bash
ssh ubuntu@192.168.0.107
ip -br addr show eth0
exit
```

Contraseña: `turtlebot`. Apunta la dirección `169.254.XXX.YYY`.

## 3. Conectar

1. Conecta el cable entre el robot y el portátil.
2. Apaga el WiFi del portátil: `nmcli radio wifi off`
3. Activa la conexión: `nmcli con up robot-cable`
4. Comprueba que llegas: `ping -c 3 169.254.XXX.YYY`
5. Solo si en el laboratorio hay más gente con robots y quieres evitar interferencias, apaga el WiFi del robot desde una sesión por cable: `ssh ubuntu@169.254.XXX.YYY` y `sudo ip link set dev wlan0 down`. **Al terminar vuelve a encenderlo**: `sudo ip link set dev wlan0 up`.

## 4. Terminales

Abre la carpeta `06_mapeado_robot_fisico` en todas. Terminal 1 en el portátil (fuera del Docker), las demás dentro del Docker.

Entrar al Docker (primera vez):

```bash
xhost +local:docker
docker start ir2121_humble
```

En cada terminal de Docker:

```bash
docker exec -it ir2121_humble bash
cd ~/Documentos/GitHub/IR2121/06_mapeado_robot_fisico
```

Si Cartographer no está instalado en el contenedor: `apt update && apt install -y ros-humble-turtlebot3-cartographer ros-humble-nav2-map-server`.

| Terminal | Dónde | Comando |
| --- | --- | --- |
| 1 | portátil | `./bringup_physical.bash 169.254.XXX.YYY LDS-01 7` |
| 2 | Docker | `./extras/check_scan.bash` → debe decir OK |
| 3 | Docker | `./slam.bash` (abre RViz con Cartographer) |
| 4 | Docker | `./record.bash` |
| 5 | Docker | `./save.bash new_save` al empezar, luego `./save.bash` cada 30-60 s |
| 6 | Docker | `./teleop.bash` |

- El `7` es el `ROS_DOMAIN_ID` del robot 107. Si te toca otro robot, cambia el número en el comando del bringup **y** el `export ROS_DOMAIN_ID=7` de los demás scripts.
- Si `check_scan.bash` dice que hay casi todo ceros, corta la terminal 1 y relánzala con `LDS-02` en vez de `LDS-01`.
- Teleoperación: despacio por los pasillos, giros suaves. En RViz las paredes deben ir dibujándose seguidas; si Cartographer se pierde, vuelve atrás despacio por donde ya pasaste.
- Guarda el último mapa con `./save.bash` **antes** de cerrar Cartographer. Quedan `map_00`, `map_01`, `map_02`… (`.pgm` + `.yaml`).
- Para la grabación con `Ctrl+C` en la terminal 4 y comprueba: `ros2 bag info rosbag_mapping_...`.
- Comprimir: `zip -r rosbag_mapping.zip rosbag_mapping_.../`

## 5. Al terminar

Enciende el WiFi del robot si lo apagaste, y el de tu portátil: `nmcli radio wifi on`.

Con los `map_XX` guardados, el PDF con la secuencia de mapas y el último superpuesto sobre el plano del TD se hace aparte.
