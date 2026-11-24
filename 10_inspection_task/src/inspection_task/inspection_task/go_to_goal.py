import math
import rclpy
from action_msgs.msg import GoalStatus, GoalStatusArray
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from tf2_ros import Buffer, TransformListener


class GoToGoal(Node):

    def __init__(self):
        super().__init__('go_to_goal')
        self.declare_parameter('x', 0.5)
        self.declare_parameter('y', 0.5)
        self.declare_parameter('yaw', 0.0)
        self.declare_parameter('tolerance', 0.3)
        self.declare_parameter('settle_time', 1.5)
        self.declare_parameter('goal_timeout', 120.0)
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('robot_frame', 'base_footprint')

        self.goals = [[self.get_parameter('x').value, self.get_parameter('y').value, self.get_parameter('yaw').value]]
        self.tolerance = self.get_parameter('tolerance').value
        self.settle_time = self.get_parameter('settle_time').value
        self.goal_timeout = self.get_parameter('goal_timeout').value
        self.map_frame = self.get_parameter('map_frame').value
        self.robot_frame = self.get_parameter('robot_frame').value

        self.goal_pub = self.create_publisher(PoseStamped, '/goal_pose', 10)
        status_qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.create_subscription(GoalStatusArray, '/navigate_to_pose/_action/status', self.on_status, status_qos)
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.index = 0
        self.state = 'wait'
        self.known_ids = set()
        self.goal_status = None
        self.results = []
        self.finished = False
        self.last_wait_log = None
        self.create_timer(0.2, self.loop)

    def now(self):
        return self.get_clock().now()

    def seconds_since(self, t):
        return (self.now() - t).nanoseconds / 1e9

    def robot_xy(self):
        try:
            t = self.tf_buffer.lookup_transform(self.map_frame, self.robot_frame, rclpy.time.Time())
        except Exception:
            return None
        return t.transform.translation.x, t.transform.translation.y

    def on_status(self, msg):
        ids = [bytes(s.goal_info.goal_id.uuid) for s in msg.status_list]
        if self.state != 'moving':
            self.known_ids.update(ids)
            return
        for s in reversed(msg.status_list):
            if bytes(s.goal_info.goal_id.uuid) not in self.known_ids:
                self.goal_status = s.status
                return

    def send_goal(self):
        x, y, yaw = self.goals[self.index]
        msg = PoseStamped()
        msg.header.frame_id = self.map_frame
        msg.header.stamp = self.now().to_msg()
        msg.pose.position.x = float(x)
        msg.pose.position.y = float(y)
        msg.pose.orientation.z = math.sin(yaw / 2.0)
        msg.pose.orientation.w = math.cos(yaw / 2.0)
        self.goal_status = None
        self.goal_pub.publish(msg)
        self.goal_start = self.now()
        self.still_xy = None
        self.still_since = None
        self.state = 'moving'
        self.get_logger().info(f'Objetivo {self.index + 1}/{len(self.goals)}: x={x:.2f} y={y:.2f} yaw={yaw:.2f}')

    def arrived_by_distance(self, xy):
        x, y, _ = self.goals[self.index]
        if math.hypot(xy[0] - x, xy[1] - y) > self.tolerance:
            self.still_xy = None
            return False
        if self.still_xy is None or math.hypot(xy[0] - self.still_xy[0], xy[1] - self.still_xy[1]) > 0.02:
            self.still_xy = xy
            self.still_since = self.now()
            return False
        return self.seconds_since(self.still_since) >= self.settle_time

    def finish_goal(self, ok, reason):
        x, y, _ = self.goals[self.index]
        self.results.append((self.index + 1, x, y, ok, reason))
        if ok:
            self.get_logger().info(f'Objetivo {self.index + 1} alcanzado ({reason})')
        else:
            self.get_logger().warn(f'Objetivo {self.index + 1} no alcanzado ({reason})')
        self.next_goal()

    def next_goal(self):
        self.index += 1
        self.state = 'send' if self.index < len(self.goals) else 'done'

    def loop(self):
        if self.state == 'wait':
            if self.goal_pub.get_subscription_count() > 0 and self.robot_xy() is not None:
                self.state = 'send'
            elif self.last_wait_log is None or self.seconds_since(self.last_wait_log) > 5.0:
                self.last_wait_log = self.now()
                self.get_logger().info('Esperando a Nav2 y a la pose inicial (map -> base_footprint)')
            return
        if self.state == 'send':
            self.send_goal()
            return
        if self.state == 'moving':
            if self.goal_status == GoalStatus.STATUS_SUCCEEDED:
                self.finish_goal(True, 'Nav2 SUCCEEDED')
            elif self.goal_status in (GoalStatus.STATUS_ABORTED, GoalStatus.STATUS_CANCELED):
                self.finish_goal(False, 'Nav2 ABORTED' if self.goal_status == GoalStatus.STATUS_ABORTED else 'Nav2 CANCELED')
            elif self.seconds_since(self.goal_start) > self.goal_timeout:
                self.finish_goal(False, 'tiempo agotado')
            else:
                xy = self.robot_xy()
                if xy is not None and self.arrived_by_distance(xy):
                    self.finish_goal(True, 'distancia')
            return
        if self.state == 'done' and not self.finished:
            ok = sum(1 for r in self.results if r[3])
            self.get_logger().info(f'Navegación terminada: {ok}/{len(self.goals)} objetivos alcanzados')
            for n, x, y, good, reason in self.results:
                self.get_logger().info(f'  {n}: ({x:.2f}, {y:.2f}) {"OK" if good else "FALLO"} - {reason}')
            self.finished = True


def main():
    rclpy.init()
    node = GoToGoal()
    try:
        while rclpy.ok() and not node.finished:
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == '__main__':
    main()
