#en esta forma no crea copias distintas, sustituye al original ./map
#source /opt/ros/humble/setup.bash
#export ROS_LOCALHOST_ONLY=1
#ros2 run nav2_map_server map_saver_cli -f ./map

#!/bin/bash

# Cargar el entorno de ROS 2
source /opt/ros/humble/setup.bash
export ROS_LOCALHOST_ONLY=1

# Archivo donde guardaremos el contador
COUNTER_FILE=".map_counter"

# Si se pasa "new_save" como primer argumento, reiniciamos el contador
if [ "$1" == "new_save" ]; then
    echo "0" > "$COUNTER_FILE"
    echo "Reiniciando el contador de mapas..."
fi

# Leer el contador actual (si el archivo no existe, empezamos en 0)
if [ -f "$COUNTER_FILE" ]; then
    COUNTER=$(cat "$COUNTER_FILE")
else
    COUNTER=0
fi

# Asignar el nombre del mapa dependiendo del contador
if [ "$COUNTER" -eq 0 ]; then
    MAP_NAME="map"
else
    MAP_NAME="map${COUNTER}"
fi

echo "Guardando el mapa como: ./$MAP_NAME"

# Ejecutar el guardado del mapa con el nuevo nombre
ros2 run nav2_map_server map_saver_cli -f "./$MAP_NAME"

# Sumar 1 al contador y guardarlo para la próxima vez
NEXT_COUNTER=$((COUNTER + 1))
echo "$NEXT_COUNTER" > "$COUNTER_FILE"
