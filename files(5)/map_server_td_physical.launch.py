import os
import yaml
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import ExecuteProcess
from launch.substitutions import LaunchConfiguration
import launch_ros.actions

def generate_launch_description():

	ld = LaunchDescription()

	map_file_path = '../TD_n1.yaml'

	map_server_cmd = Node(
		package='nav2_map_server',
		executable='map_server',
		output='screen',
		parameters=[{'yaml_filename': map_file_path}])


	lifecycle_nodes = ['map_server']
	use_sim_time = False
	autostart = True

	start_lifecycle_manager_cmd = launch_ros.actions.Node(
		    package='nav2_lifecycle_manager',
		    executable='lifecycle_manager',
		    name='lifecycle_manager',
		    output='screen',
		    emulate_tty=True,
		    parameters=[{'use_sim_time': use_sim_time},
		                {'autostart': autostart},
		                {'node_names': lifecycle_nodes}])

	ld.add_action(map_server_cmd)
	ld.add_action(start_lifecycle_manager_cmd)

	return ld
