import os

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    map_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'rooms.yaml')

    map_server_cmd = Node(
        package='nav2_map_server',
        executable='map_server',
        name='map_server',
        output='screen',
        parameters=[{'yaml_filename': map_file_path}])

    lifecycle_manager_cmd = Node(
        package='nav2_lifecycle_manager',
        executable='lifecycle_manager',
        name='lifecycle_manager_map',
        output='screen',
        parameters=[{'autostart': True},
                    {'node_names': ['map_server']}])

    ld = LaunchDescription()
    ld.add_action(map_server_cmd)
    ld.add_action(lifecycle_manager_cmd)
    return ld
