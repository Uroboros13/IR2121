from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    ld = LaunchDescription()
    map_file_path = '../rooms.yaml' # CAMBIAR AL MAPA QUE QUERAMOS ABRIR
    
    map_server_cmd = Node(
        package='nav2_map_server',
        executable='map_server',
        output='screen',
        parameters=[{'yaml_filename': map_file_path}]
    )
    
    ld.add_action(map_server_cmd)
    return ld
