import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration

TURTLEBOT3_MODEL = os.environ.get('TURTLEBOT3_MODEL', 'burger')
HERE = os.path.dirname(os.path.realpath(__file__))


def default_params():
    pkg = get_package_share_directory('turtlebot3_navigation2')
    name = TURTLEBOT3_MODEL + '.yaml'
    for path in (os.path.join(pkg, 'param', 'humble', name), os.path.join(pkg, 'param', name)):
        if os.path.exists(path):
            return path
    return os.path.join(get_package_share_directory('nav2_bringup'), 'params', 'nav2_params.yaml')


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    map_yaml = LaunchConfiguration('map')
    params_file = LaunchConfiguration('params_file')
    initial_x = LaunchConfiguration('initial_x')
    initial_y = LaunchConfiguration('initial_y')

    nav2_launch_file_dir = os.path.join(get_package_share_directory('nav2_bringup'), 'launch')

    initial_pose = [
        '{header: {frame_id: map}, pose: {pose: {position: {x: ', initial_x, ', y: ', initial_y,
        ', z: 0.0}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}, covariance: ',
        '[0.25, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.25, 0.0, 0.0, 0.0, 0.0, '
        '0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, '
        '0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0685]}}',
    ]

    return LaunchDescription([
        DeclareLaunchArgument(
            'map',
            default_value=os.path.join(HERE, 'rooms.yaml'),
            description='Full path to map file to load'),

        DeclareLaunchArgument(
            'params_file',
            default_value=default_params(),
            description='Full path to param file to load'),

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation (Gazebo) clock if true'),

        DeclareLaunchArgument(
            'initial_x',
            default_value='2.5',
            description='Initial x position of the robot in the map frame'),

        DeclareLaunchArgument(
            'initial_y',
            default_value='2.5',
            description='Initial y position of the robot in the map frame'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(nav2_launch_file_dir, 'bringup_launch.py')),
            launch_arguments={
                'map': map_yaml,
                'use_sim_time': use_sim_time,
                'params_file': params_file}.items(),
        ),

        TimerAction(
            period=10.0,
            actions=[
                ExecuteProcess(
                    cmd=['ros2', 'topic', 'pub', '-w', '1', '-t', '3', '-r', '1',
                         '/initialpose', 'geometry_msgs/msg/PoseWithCovarianceStamped',
                         initial_pose],
                    output='screen'),
            ]),
    ])
