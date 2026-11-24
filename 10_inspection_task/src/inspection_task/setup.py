from setuptools import setup

package_name = 'inspection_task'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ulisses',
    maintainer_email='ulisses@todo.todo',
    description='Inspection task: TurtleBot3 navigation to a list of goals with Nav2',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'go_to_goal = inspection_task.go_to_goal:main',
        ],
    },
)
