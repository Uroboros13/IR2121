**23/11/2026** 
*Herramienta IA usada:* Gemini modelo Neon
*Prompt:* 
Soy estudiante de robótica (nivel de 1.º). Uso ROS 2 Humble con TurtleBot3 y hasta ahora solo he lanzado cosas ya hechas con "ros2 launch" y "ros2 run" desde scripts de bash. Ahora tengo que escribir mi propio programa en Python que mande objetivos al robot, y el profesor dice que tiene que ser un "paquete de ROS 2" con un "nodo".

No sé qué es un paquete ni cómo se crea, y no recuerdo haberlo hecho nunca. Explícamelo desde cero y con palabras sencillas:
1. Qué es un paquete y qué es un nodo, y en qué se diferencian de un script de Python normal.
2. Qué pasos hay que seguir para crear un paquete, meter mi programa dentro y ejecutarlo con "ros2 run" (solo los comandos y para qué sirve cada uno).
3. Qué archivos aparecen en un paquete y cuáles tendría que tocar yo.
No escribas mi programa; usa un ejemplo mínimo tipo "hola mundo".

*Output:* 
Cuando usabas `ros2 run` o `ros2 launch`, estabas ejecutando programas que alguien ya había empaquetado para que ROS 2 supiera dónde encontrarlos. Ahora te toca a ti pasar al otro lado.

## 1. Paquete, nodo y script normal: ¿en qué se diferencian?

* **Un script de Python normal (`programa.py`):** Es un archivo suelto que ejecutas con `python3 programa.py`. Vive aislado; no sabe que existe un robot ni puede hablar fácilmente con otros programas de ROS 2.
* **Un nodo:** Es un programa en ejecución conectado a la red de ROS 2. Por dentro es un archivo de Python, pero usa la librería de ROS 2 (`rclpy`) para presentarse al sistema y comunicarse con otros nodos (por ejemplo, para decirle a los motores del TurtleBot3 que se muevan).
* **Un paquete:** Es simplemente una **carpeta organizada con unas reglas concretas**. Contiene tus nodos (tu código) y un par de archivos de configuración que le dicen a ROS 2 cómo se llama tu proyecto, qué librerías necesita y qué comando debe ejecutar cuando escribas `ros2 run`.

> **Resumen mental:** El **paquete** es la caja etiquetada; el **nodo** es el programa que va dentro y sabe hablar el idioma de ROS 2.

---

## 2. Pasos para crear tu paquete y ejecutar un "Hola Mundo"

En ROS 2 todo vive dentro de una carpeta de trabajo llamada *workspace* (normalmente `~/ros2_ws`). Sigue este orden exacto:

1. **Ir a la carpeta src de tu workspace:** Si no tienes workspace, créalo primero con mkdir -p ~/ros2_ws/src.
Todos tus paquetes propios deben ir siempre dentro de `src`:

```bash
cd ~/ros2_ws/src

```


2. **Crear el paquete de Python:**
Usa el comando de ROS 2 para generar la estructura vacía. Aquí llamaremos al paquete `mi_paquete` y le diremos que usará `rclpy` (la librería de ROS 2 para Python):

```bash
ros2 pkg create --build-type ament_python --dependencies rclpy mi_paquete

```


3. **Crear tu archivo de nodo (Hola Mundo):**
Dentro de `mi_paquete/mi_paquete/`, crea un archivo llamado `hola_nodo.py` con este código mínimo:

```python
import rclpy
from rclpy.node import Node

class HolaNodo(Node):
    def __init__(self):
        super().__init__('hola_nodo')
        self.get_logger().info('¡Hola mundo desde ROS 2!')

def main(args=None):
    rclpy.init(args=args)
    nodo = HolaNodo()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

```


4. **Registrar el nodo en setup.py:** Sin este paso, ros2 run no encontrará tu programa.
Abre `mi_paquete/setup.py`, busca la sección `entry_points` y añade tu nodo dentro de `console_scripts`:

```python
entry_points={
    'console_scripts': [
        'hola_nodo = mi_paquete.hola_nodo:main',
    ],
},

```

Esto le dice a ROS 2: *"Cuando el usuario escriba `hola_nodo`, ejecuta la función `main` del archivo `hola_nodo.py` que está dentro de `mi_paquete`"*.


5. **Compilar el paquete:** Hazlo siempre desde la raíz del workspace, nunca desde src.
Vuelve a la raíz de tu workspace y compila para que ROS 2 registre tu nuevo paquete:

```bash
cd ~/ros2_ws
colcon build --packages-select mi_paquete

```


6. **Cargar el entorno (source):** Obligatorio en cada terminal nueva que abras.
Avisa a tu terminal de que acaba de aparecer un paquete nuevo:

```bash
source install/setup.bash

```


7. **Ejecutar tu nodo:**
Ahora ya puedes lanzarlo igual que hacías con los programas del profesor:

```bash
ros2 run mi_paquete hola_nodo

```


---

## 3. Qué archivos aparecen en el paquete y cuáles tienes que tocar

Al ejecutar `ros2 pkg create`, verás que se crean varias carpetas y archivos automáticamente. No te agobies: la mayoría no se tocan nunca.

| Archivo o carpeta | Para qué sirve | ¿Tienes que tocarlo? |
| --- | --- | --- |
| **`mi_paquete/hola_nodo.py`** | Tu programa de Python (el nodo). | **Sí.** Aquí escribes tu código. |
| **`setup.py`** | Le dice a Python y a ROS 2 qué nodos existen para poder usar `ros2 run`. | **Sí.** Cada vez que añadas un nodo nuevo, lo registras en `console_scripts`. |
| **`package.xml`** | Ficha técnica del paquete: nombre, autor y dependencias (librerías de ROS 2 que usas). | **Solo a veces.** Si más adelante usas mensajes especiales (como `geometry_msgs` para mover el robot), los añades aquí. |
| **`mi_paquete/__init__.py`** | Archivo vacío que le indica a Python que esa carpeta es un módulo. | **No.** Déjalo vacío. |
| **`setup.cfg`** | Configuración interna para que `colcon` sepa dónde instalar los scripts. | **No.** |
| **`resource/mi_paquete`** | Archivo marcador para que ROS 2 indexe el paquete. | **No.** |
| **`test/`** | Carpeta para pruebas automáticas de código. | **No** (de momento). |

*Uso del output en esta tarea*
se ha creado temporalmente el fichero de "hola mundo" para verificar y terminar de comprender la tarea a realizar y el paquete de ROS 2, dicho fichero fue modificado hasta convertirse en go_to_goal.py
