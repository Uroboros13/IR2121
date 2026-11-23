# Homework: comparación de SLAM en Gazebo (modelo TD)

Copia esta carpeta en `~/Documentos/GitHub/IR2121/homework_slam`. Todo se ejecuta **dentro del Docker `ir2121_humble`** y **desde esta carpeta**.

```bash
xhost +local:docker
docker start ir2121_humble
docker exec -it ir2121_humble bash
cd ~/Documentos/GitHub/IR2121/homework_slam
```

## 0. Instalar (una vez)

```bash
./0_instalar.bash
```

## 1. Grabar el bag (3 terminales)

| Terminal | Comando |
| --- | --- |
| 1 | `./1_gazebo.bash X Y` (mundo vacío + robot en X,Y + modelo TD_n1 en el origen) |
| 2 | `./3_grabar.bash` (graba `/clock /odom /robot_description /scan /tf /tf_static`) |
| 3 | `./2_teleop.bash` |

- `1_gazebo.bash` copia el modelo de `../Nuevo Carpeta para cosas Nuevas/Worlds/models/TD_n1` si no está aquí.
- `X Y` es dónde aparece el robot. Si cae dentro de una pared, muévelo en Gazebo con la herramienta de mover, o vuelve a lanzar con otras coordenadas.
- Recorre los pasillos despacio durante 5–10 min y vuelve a pasar por sitios ya vistos: así se nota cómo cierra bucles cada algoritmo.
- Para la grabación con `Ctrl+C` en la terminal 2 y **cierra Gazebo** antes de seguir.

## 2. SLAM sobre el bag (1 terminal, Gazebo cerrado)

```bash
./5_comparar.bash rosbag_td_AAAA_MM_DD-HH_MM_SS
```

Ejecuta uno tras otro Cartographer, SLAM Toolbox y RTAB-Map sobre el mismo bag, guardando un mapa cada 20 s en `mapas_cartographer/`, `mapas_toolbox/` y `mapas_rtabmap/`. Cada carpeta lleva su `slam.log`.

- Un solo algoritmo: `./4_slam.bash toolbox rosbag_td_...`
- Más rápido o con otro intervalo: `./5_comparar.bash rosbag_td_... 2 10` (doble velocidad, un mapa cada 10 s)

## 3. Entrega

1. Escribe los comentarios de cada algoritmo en `comentarios.txt`, en las secciones `[cartographer]`, `[toolbox]`, `[rtabmap]` y `[conclusion]`.
2. Genera el PDF y el zip del bag:
   ```bash
   ./7_entrega.bash rosbag_td_AAAA_MM_DD-HH_MM_SS
   ```
   Quedan en `entrega/`: `rosbag_td_….zip` y `comparacion_SLAM_gazebo.pdf`.

El PDF lleva la portada, la secuencia de mapas de cada algoritmo (9 por página), su mapa final con tus comentarios y una página con los tres mapas finales lado a lado.
