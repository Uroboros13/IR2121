import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

HERE = os.path.dirname(os.path.realpath(__file__))
TI_MODEL = os.path.join(HERE, '..', 'models', 'TI_n1', 'model.sdf')


def generate_launch_description():
    x_pose = LaunchConfiguration('x_pose')
    y_pose = LaunchConfiguration('y_pose')
    empty_world = os.path.join(
        get_package_share_directory('turtlebot3_gazebo'), 'launch', 'empty_world.launch.py')

    return LaunchDescription([
        DeclareLaunchArgument('x_pose', default_value='0.0'),
        DeclareLaunchArgument('y_pose', default_value='0.0'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(empty_world),
            launch_arguments={'x_pose': x_pose, 'y_pose': y_pose}.items(),
        ),

        TimerAction(period=5.0, actions=[
            Node(
                package='gazebo_ros',
                executable='spawn_entity.py',
                arguments=['-entity', 'TI_n1', '-file', TI_MODEL, '-x', '0', '-y', '0', '-z', '0'],
                output='screen',
            ),
        ]),
    ])
