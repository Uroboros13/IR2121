# Mando TB3: controlar el TurtleBot3 desde el móvil

El móvil se conecta al robot por cable USB con «Compartir conexión por USB». La app tiene un botón por script, un joystick para conducir y una vista del mapa.

Son dos piezas:

- **`robot/`**: un pequeño servidor que corre en el propio robot. Solo usa Python y ROS 2 Humble, que ya están instalados.
- **`android/MandoTB3.apk`**: la app del móvil, Android 5 o superior.

## 1. Instalar en el robot (una vez, con el portátil)

Conecta el portátil al robot por cable como siempre (`nmcli con up robot-cable`) y copia la carpeta:

```bash
cd ~/Documentos/GitHub/IR2121/extras/tb3_mando
scp -r robot ubuntu@169.254.92.124:~/tb3_phone
ssh ubuntu@169.254.92.124
bash ~/tb3_phone/install_robot.bash 10 LDS-01 --usb
```

- `10` es el `ROS_DOMAIN_ID` y `LDS-01` el láser del robot 110. Para otro robot, cambia ambos.
- `--usb` configura el robot para que coja IP cuando le enchufas el móvil con «Compartir conexión por USB». Pide la contraseña de `sudo` (`turtlebot`). Sin esa opción, el móvil no tendrá red con el robot.
- Al terminar muestra el **PIN** de 6 cifras. Apúntalo: la app lo pide la primera vez.
- El servidor arranca solo cada vez que se enciende el robot, unos 20 s después.

Para quitarlo todo del robot: `bash ~/tb3_phone/uninstall_robot.bash`.

### Si el robot se olvida de todo al apagarlo

Con el portátil conectado al robot por cable (`nmcli con up robot-cable`):

```bash
cd ~/Documentos/GitHub/IR2121/extras/tb3_mando
./preparar_robot.bash
```

Copia el servidor al robot y lo arranca en modo temporal. Siempre deja el mismo PIN, `131576`, para que la app no te lo vuelva a pedir. También deja vigilando `usb0`: en cuanto enchufas el móvil con «Compartir conexión por USB», el robot pide IP solo, sin `sudo dhclient usb0`. Pide la contraseña `turtlebot` dos veces, una para entrar y otra para `sudo`.

Para otro robot, pasa la IP de cable, el `ROS_DOMAIN_ID`, el láser y el PIN: `./preparar_robot.bash 169.254.X.Y 7 LDS-02 131576`.

## 2. Instalar la app en el móvil

Pasa `android/MandoTB3.apk` al móvil y ábrelo. Android pedirá permiso para instalar apps de origen desconocido. También puede avisar de que la app es para una versión antigua de Android; se puede instalar igual.

## 3. Usarla

1. Enciende el robot y espera un minuto.
2. Conecta el móvil al USB de la Raspberry del robot.
3. En el móvil: *Ajustes → Redes → Compartir conexión → Compartir conexión por USB* (el nombre cambia un poco según la marca).
4. Abre **Mando TB3**, pulsa **Buscar robot**, toca el robot que aparece y escribe el PIN.

Los botones siguen el orden de siempre:

| Botón | Equivale a | Notas |
| --- | --- | --- |
| 1 · Bringup | `launch_turtlebot.bash` | No arranca si ya hay otro bringup en marcha: dos a la vez rompen los motores y el LIDAR |
| 2 · Comprobar láser | `check_scan.bash` | El estado también muestra los Hz y las medidas válidas en directo |
| 3 · SLAM | `slam.bash` | Cartographer sin RViz, en el robot. Si no está instalado, sale «no instalado» |
| 4 · Grabar bag | `record.bash` | Mismos topics. El bag se guarda en el robot |
| 5 · Autoguardado | `auto_save.bash` | Cada N segundos. La casilla *new_save* vuelve a `map_00` |
| Guardar mapa ahora | `save.bash` | |
| Parar todo | — | Para en orden: robot, autoguardado, grabación, SLAM y bringup |
| Apagar robot | `sudo poweroff` | Pulsa dos veces. Para todo y apaga. Espera a que la luz verde deje de parpadear para darle al interruptor |
| 6 · Joystick | `teleop.bash` | Al soltar se para. Si se corta la conexión, el robot se para solo en 0,5 s |
| 6 · Teclas W A S D X Z | `teleop.bash` | Como `teleop_keyboard`: cada pulsación sube o baja la velocidad y se mantiene. Z quita el giro para ir recto y S para |

Todo lo que se graba queda en el robot, en `~/tb3_phone/datos/` (bags, `map_XX.pgm/.yaml` y los logs de cada botón).

### Guardar los datos en el móvil

En el panel **Guardar en el móvil**, pulsa *Ver datos del robot* y luego *Descargar* en lo que quieras:

- **Todo**: todos los bags, los mapas y los logs en un solo `.zip`.
- **Mapas y logs**: solo los `map_XX` y los logs, ocupa poco.
- **Cada bag** por separado.

Se guarda en *Descargas/TB3* del móvil, con un `info.txt` del robot, el `ROS_DOMAIN_ID` y el láser. Dentro del zip, los bags quedan tal cual, listos para `ros2 bag info` y `ros2 bag play`. El bag que se está grabando no se puede descargar: para la grabación antes.

También puedes traerlo al portátil por cable:

```bash
scp -r ubuntu@169.254.92.124:~/tb3_phone/datos ~/Documentos/GitHub/IR2121/07_mapeado_FCS/extras/movil
```

## 4. Limitaciones

- **SLAM en el robot:** la imagen del TurtleBot3 no suele traer Cartographer. Con el móvil compartiendo Internet se puede instalar en el robot: `sudo apt install ros-humble-cartographer-ros ros-humble-turtlebot3-cartographer`. Correr Cartographer y grabar a la vez exige bastante a la Raspberry.
- **Guardar mapas:** si `nav2_map_server` no está en el robot, el servidor escribe él mismo el `.pgm` y el `.yaml`, en el mismo formato que `map_saver_cli`.
- **Alimentación:** el móvil se carga desde el USB de la Raspberry. Si el robot se reinicia o va raro, prueba con el móvil bien cargado o con un cable que no cargue.
- **Seguridad:** el PIN evita que otro en la misma red WiFi mueva el robot. La velocidad máxima es 0,22 m/s y 2 rad/s (`max_lin` y `max_ang` en `~/tb3_phone/config.json`).
- **Robots del laboratorio:** el instalador añade una línea al `crontab` y un fichero de red en `/etc/systemd/network`. Pregunta al profesor antes de instalarlo en un robot compartido, y quítalo con `uninstall_robot.bash` al acabar.

## 5. Volver a compilar la APK

En Ubuntu, con `sudo apt install android-sdk-platform-23 aapt dalvik-exchange zipalign apksigner default-jdk`:

```bash
bash android/build_apk.bash
```

Firma siempre con `android/tb3mando.keystore` (contraseña `ir2121`). Si cambias la clave, Android no deja actualizar encima y hay que desinstalar la app antes.
