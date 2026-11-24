# Inspection task · TurtleBot3 + Nav2 (ROS 2 Humble)

Nodo de ROS 2 en Python (`go_to_goal`) que envía un objetivo al robot por `/goal_pose` y espera a que Nav2 lo alcance.

**Versión 1:** un único objetivo. Se considera alcanzado cuando el estado en `/navigate_to_pose/_action/status` es `SUCCEEDED`, o cuando el robot está a menos de `tolerance` del objetivo (tf `map → base_footprint`) y se queda quieto `settle_time` segundos.

| Ruta | Qué es |
| --- | --- |
| `src/inspection_task/` | Paquete ROS 2 (ament_python) con el nodo `go_to_goal` |
| `compilar.bash` | Compila el paquete con `colcon build` |
| `ejecutar.bash` | Ejecuta `go_to_goal`: `./ejecutar.bash X Y YAW` |
| `simulacion/` | Scripts para Gazebo con waffle_pi en `turtlebot3_world`, y mapa de ese mundo (`maps/`) |
| `TD_n1/`, `mapa_sim/` | Modelo y mapa del mundo TD_n1 |
| `launch_amcl_sim.bash`, `send_goal.txt` | Localización AMCL en TD_n1 y ejemplo de objetivo a mano |

## Ejecución en simulación

Cada orden en una terminal, desde esta carpeta:

| Terminal | Orden | Esperar a |
| --- | --- | --- |
| 1 | `simulacion/1_simulacion.bash` (o `simulacion/1_simulacion.bash sin_gui`) | `Successfully spawned entity` |
| 2 | `simulacion/2_navegacion.bash` | RViz con el mapa |
| 3 | `simulacion/3_pose_inicial.bash` | `Managed nodes are active` de la navegación |
| 4 | `./compilar.bash` y `./ejecutar.bash 0.55 0.55 0` | `Objetivo 1 alcanzado` |

- Cámara: `simulacion/4_camara.bash`
- Objetivo a mano: `simulacion/5_objetivo_manual.bash X Y`
- Teleoperación: `simulacion/6_teleop.bash`
- Robot real: `USE_SIM_TIME=false ./ejecutar.bash X Y YAW`
