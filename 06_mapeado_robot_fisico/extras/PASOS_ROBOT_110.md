# Mapear con el robot 110 por cable

Pasos para repetir el mapeo con el portátil (Ubuntu 24.04), el robot 110 y los scripts de esta carpeta. Todo lo de ROS se ejecuta dentro del Docker `ir2121_humble`, salvo el bringup, que se lanza desde el portátil y corre en el robot.

| Dato | Valor |
| --- | --- |
| Robot | `tb3-110`, burger |
| LIDAR | `LDS-01` |
| `ROS_DOMAIN_ID` | `10` (ya puesto en los scripts) |
| IP WiFi | `192.168.0.110` |
| IP de cable | `169.254.92.124` (compruébala, puede cambiar) |
| Usuario y contraseña | `ubuntu` / `turtlebot` |

## 1. Encender y conectar

1. Pon una batería cargada, enciende el robot y espera un minuto.
2. Conecta el cable entre el robot y el portátil.
3. Activa la conexión del portátil. Ya está creada, no hace falta repetir `nmcli con add`:

   ```bash
   nmcli con up robot-cable
   ping -c 3 169.254.92.124
   ```

El WiFi del portátil puede quedarse encendido. Por cable ha funcionado así.

**Si el ping falla**, comprueba la IP de cable desde un PC del laboratorio:

```bash
ssh ubuntu@192.168.0.110
ip -br addr show eth0
exit
```

Usa la dirección `169.254.x.y` que aparezca, sin el `/16`, en lugar de `169.254.92.124`.

## 2. Preparar Docker

Una vez, en una terminal del portátil:

```bash
xhost +local:docker
docker start ir2121_humble
```

## 3. Terminales

Abre una terminal del portátil para el bringup:

```bash
cd ~/Documentos/GitHub/IR2121/06_mapeado_robot_fisico
./bringup_physical.bash 169.254.92.124 LDS-01 10
```

Pedirá la contraseña. Espera a que aparezca `Run!` y déjala abierta.

**Lanza un solo bringup.** Dos a la vez se pelean por los puertos del robot: el nodo de los motores se cae y el LIDAR pierde datos. Si dudas de si ya hay uno en marcha, compruébalo por SSH antes de lanzarlo; si esto no muestra nada, no hay ninguno:

```bash
ssh ubuntu@169.254.92.124 'pgrep -a -f "ros2 laun[c]h turtlebot3_bringup"'
```

En cada una de las demás terminales entra primero al Docker:

```bash
docker exec -it ir2121_humble bash
cd ~/Documentos/GitHub/IR2121/06_mapeado_robot_fisico
```

| Terminal | Comando | Para qué |
| --- | --- | --- |
| 2 | `./extras/check_scan.bash` | Comprobar el LIDAR antes de empezar |
| 3 | `./slam.bash` | Cartographer y RViz |
| 4 | `./record.bash` | Grabar el bag, antes de conducir |
| 5 | `./extras/auto_save.bash 45 new_save` | Guardar un mapa cada 45 s |
| 6 | `./teleop.bash` | Conducir el robot |

**`check_scan.bash`:** debe mostrar unos 5 Hz. Con el robot en una zona abierta puede decir `MAL: casi todo ceros` con unas 110 medidas válidas, por debajo del umbral de 150. En esa prueba, RViz dibujó las paredes y el mapa salió bien. Con cerca de 0 medidas válidas o menos de 4 Hz hay un problema real: no sigas.

**Conducción:** ve despacio y gira con suavidad. En RViz las paredes deben dibujarse seguidas. Si Cartographer se pierde, vuelve despacio por donde ya pasaste.

## 4. Guardar mapas

`auto_save.bash` llama a `save.bash` cada cierto tiempo, así que crea los mismos `map_00`, `map_01`, `map_02`… (`.pgm` + `.yaml`) y usa el mismo contador `.map_counter`.

| Comando | Qué hace |
| --- | --- |
| `./extras/auto_save.bash` | Guarda cada 45 s y sigue la numeración actual |
| `./extras/auto_save.bash 30` | Guarda cada 30 s y sigue la numeración actual |
| `./extras/auto_save.bash 45 new_save` | Reinicia la numeración desde `map_00` y guarda cada 45 s |

Con `Ctrl+C` guarda un último mapa y termina. Si un guardado falla, avisa, no gasta número y reintenta en el siguiente ciclo.

**Cuidado:** `new_save` vuelve a `map_00` y **sobrescribe** los mapas que ya existan con esos nombres. Úsalo solo al empezar una sesión nueva.

Sigues pudiendo guardar a mano con `./save.bash`, pero mejor con `auto_save.bash` parado, para que no coincidan los dos.

## 5. Terminar, en este orden

1. **Teleop:** para el robot y pulsa `Ctrl+C`.
2. **`auto_save.bash`:** `Ctrl+C`. Guarda el último mapa, y por eso debe pararse antes que `slam.bash`.
3. **`record.bash`:** `Ctrl+C`.
4. **`slam.bash`:** `Ctrl+C`.
5. **Bringup:** `Ctrl+C`.

Comprueba el bag dentro del Docker. Todos los topics deben tener mensajes y `/scan`, unos 5 Hz:

```bash
source /opt/ros/humble/setup.bash
ros2 bag info rosbag_mapping_...
```

Comprímelo desde una terminal del portátil, porque el Docker no tiene `zip`:

```bash
cd ~/Documentos/GitHub/IR2121/06_mapeado_robot_fisico
zip -r rosbag_mapping.zip rosbag_mapping_.../
```

Apaga el robot por SSH:

```bash
ssh ubuntu@169.254.92.124
sudo halt -p
```

Espera a que el LED amarillo deje de parpadear, apaga el interruptor y pon la batería a cargar.

## 6. Qué entregar

Según la Task, se suben dos ficheros:

- `rosbag_mapping.zip`
- Un PDF con la secuencia de imágenes de los mapas (`map_XX`) y la última superpuesta sobre el plano del edificio TD

Los `map_XX.pgm` y `.yaml` sirven para crear el PDF, pero no se suben sueltos. La carpeta `prueba_cable/` es solo de pruebas y no va en la entrega.

## Si algo falla

| Síntoma | Causa probable | Qué hacer |
| --- | --- | --- |
| `NO llegan mensajes de /scan` | El bringup no está en marcha o el dominio no coincide | Revisa la terminal 1 y que el dominio sea 10 |
| Unos 2,5 Hz y casi 0 medidas válidas | Fallo del LIDAR, como en el robot 107 | Cambia de robot |
| Mapa vacío con `save.bash` | Pocas medidas o `slam.bash` parado | Comprueba `check_scan.bash` y `slam.bash` |
| Teleop no mueve el robot y `Unknown topic '/cmd_vel'` | El nodo de los motores se ha caído, por ejemplo con dos bringups a la vez | Para todos los bringups y lanza uno solo |
| Todos los mapas salen iguales | Falta `/odom` o `/tf`, o Cartographer se ha parado | Revisa el bringup y reinicia `slam.bash` |
| `Permission denied` al lanzar un script | Falta el permiso de ejecución | `chmod u+x *.bash` en el portátil |

## Usar otro robot

Los robots 101-110 llevan LDS-01 y su dominio es el último número (108 → 8). Cambia el número en los scripts:

```bash
sed -i 's/^export ROS_DOMAIN_ID=.*/export ROS_DOMAIN_ID=8/' *.bash
```

Y lanza el bringup con su IP y su dominio: `./bringup_physical.bash 169.254.x.y LDS-01 8`.
