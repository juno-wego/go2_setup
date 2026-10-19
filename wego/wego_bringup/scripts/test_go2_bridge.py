"""Exercise configured bridge/URDF using synthetic states on loopback domain 91."""
import json, os, signal, subprocess, tempfile, time
from pathlib import Path
import yaml

ws = Path.home() / 'wego_ws'
config = yaml.safe_load((ws/'src/wego/wego_bringup/config/robot.yaml').read_text())
config['go2']['domain_id'] = 91
config['go2']['network_interface'] = 'lo'
config['lidar']['enabled'] = config['camera']['enabled'] = False
os.environ['ROS_DOMAIN_ID'] = '91'
os.environ['CYCLONEDDS_URI'] = '<CycloneDDS><Domain><General><Interfaces><NetworkInterface name="lo"/></Interfaces></General></Domain></CycloneDDS>'
with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
    yaml.safe_dump(config, f); f.flush()
    with (ws/'log/go2-loopback-launch.log').open('w') as log:
        process = subprocess.Popen(['ros2', 'launch', 'wego_bringup', 'bringup.launch.py', 'config_file:='+f.name, 'rviz:=false'], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            import rclpy
            from rclpy.qos import qos_profile_sensor_data
            from sensor_msgs.msg import Image, Imu, JointState, PointCloud2
            from nav_msgs.msg import Odometry
            from geometry_msgs.msg import Twist
            from go2_interface.msg import SportCmd
            from unitree_api.msg import Request, Response
            from array import array
            import cv2
            import numpy as np
            from unitree_go.msg import LowCmd, LowState, SportModeState
            from tf2_ros import Buffer, TransformListener
            rclpy.init()
            node = rclpy.create_node('wego_isolated_bridge_test')
            samples = {}
            subscriptions = []
            for topic, cls in [('/go2/imu', Imu), ('/joint_states', JointState), ('/go2/odom', Odometry)]:
                subscriptions.append(node.create_subscription(cls, topic, lambda msg, t=topic: samples.__setitem__(t,msg), qos_profile_sensor_data))
            buffer = Buffer(); listener = TransformListener(buffer, node)
            low_pub = node.create_publisher(LowState, '/lowstate', 10)
            sport_pub = node.create_publisher(SportModeState, '/lf/sportmodestate', 10)
            cloud_pub = node.create_publisher(PointCloud2, '/utlidar/cloud', 10)
            lidar_imu_pub = node.create_publisher(Imu, '/utlidar/imu', 10)
            image_response_pub = node.create_publisher(Response, '/api/videohub/response', 10)
            sensor_samples = {}
            for topic, cls in [('/go2/lidar', PointCloud2), ('/go2/lidar/imu', Imu),
                               ('/go2/low_state', LowState), ('/go2/camera/image_raw', Image)]:
                subscriptions.append(node.create_subscription(cls, topic, lambda msg, t=topic: sensor_samples.__setitem__(t,msg), qos_profile_sensor_data))
            ok, jpeg = cv2.imencode('.jpg', np.full((8, 12, 3), 120, dtype=np.uint8))
            assert ok
            def serve_image(request):
                assert request.header.identity.api_id == 1001
                response = Response()
                response.header.identity = request.header.identity
                response.binary = array('b', jpeg.tobytes())
                image_response_pub.publish(response)
            subscriptions.append(node.create_subscription(Request, '/api/videohub/request', serve_image, 10))
            cloud = PointCloud2(); cloud.header.frame_id = 'utlidar_lidar'
            cloud.width = 1; cloud.height = 1; cloud.point_step = 4; cloud.row_step = 4
            cloud.data = b'\x01\x02\x03\x04'
            lidar_imu = Imu(); lidar_imu.header.frame_id = 'utlidar_imu'; lidar_imu.angular_velocity.x = 0.25
            requests = []
            low_commands = []
            subscriptions.append(node.create_subscription(Request, '/api/sport/request', requests.append, 10))
            subscriptions.append(node.create_subscription(LowCmd, '/lowcmd', low_commands.append, 10))
            velocity_pub = node.create_publisher(Twist, '/cmd_vel', 10)
            command_pub = node.create_publisher(SportCmd, '/go2/sport_cmd', 10)
            low_command_pub = node.create_publisher(LowCmd, '/go2/low_cmd', 10)
            low = LowState(); low.imu_state.quaternion = [1.,0.,0.,0.]
            for i in range(12): low.motor_state[i].q = 0.01 * i
            sport = SportModeState(); sport.imu_state.quaternion = [1.,0.,0.,0.]; sport.position = [2.25,-1.,0.4]
            end = time.monotonic()+12
            while time.monotonic()<end:
                low_pub.publish(low); sport_pub.publish(sport)
                cloud_pub.publish(cloud); lidar_imu_pub.publish(lidar_imu)
                rclpy.spin_once(node, timeout_sec=0.1)
                if len(samples)==3 and len(sensor_samples)==4 and buffer.can_transform('odom','imu',rclpy.time.Time()): break
            assert process.poll() is None, 'Launch exited early'
            assert set(samples)=={'/go2/imu','/go2/odom','/joint_states'}, list(samples)
            assert samples['/go2/imu'].header.frame_id=='imu'
            joints=samples['/joint_states']; assert len(joints.name)==12 and abs(joints.position[11]-.11)<1e-5
            odom=samples['/go2/odom']; assert odom.header.frame_id=='odom' and odom.child_frame_id=='base_link'
            assert abs(odom.pose.pose.position.x-2.25)<1e-5 and odom.pose.pose.position.z==0.
            assert buffer.can_transform('odom','imu',rclpy.time.Time()), 'URDF/odometry TF disconnected'
            assert len(sensor_samples) == 4, 'Missing Go2 sensor output: ' + str(sensor_samples.keys())
            assert sensor_samples['/go2/lidar'].header == cloud.header
            assert bytes(sensor_samples['/go2/lidar'].data) == bytes(cloud.data)
            assert sensor_samples['/go2/lidar/imu'].angular_velocity.x == 0.25
            assert abs(sensor_samples['/go2/low_state'].motor_state[11].q - low.motor_state[11].q) < 1e-6
            assert sensor_samples['/go2/camera/image_raw'].width == 12
            assert 'go2_cmd_vel_bridge' in node.get_node_names(), 'Control bridge missing'
            idle_end = time.monotonic() + 0.75
            while time.monotonic() < idle_end:
                rclpy.spin_once(node, timeout_sec=0.1)
            assert not requests and not low_commands, 'Unexpected automatic command at startup'

            velocity = Twist(); velocity.linear.x = 0.12; velocity.angular.z = 0.2
            end = time.monotonic() + 4
            while time.monotonic() < end and not any(m.header.identity.api_id == 1008 for m in requests):
                velocity_pub.publish(velocity)
                rclpy.spin_once(node, timeout_sec=0.1)
            moves = [m for m in requests if m.header.identity.api_id == 1008]
            assert moves, '/cmd_vel was not forwarded'
            move = json.loads(moves[-1].parameter)
            assert abs(move['x'] - 0.12) < 1e-6 and abs(move['z'] - 0.2) < 1e-6
            end = time.monotonic() + 1.0
            while time.monotonic() < end:
                rclpy.spin_once(node, timeout_sec=0.1)
            assert sum(m.header.identity.api_id == 1003 for m in requests) == 1, 'Missing or repeated timeout stop'

            command = SportCmd(); command.command = 'euler'; command.roll = 0.1
            end = time.monotonic() + 4
            while time.monotonic() < end and not any(m.header.identity.api_id == 1007 for m in requests):
                command_pub.publish(command)
                rclpy.spin_once(node, timeout_sec=0.1)
            assert any(m.header.identity.api_id == 1007 for m in requests), '/go2/sport_cmd was not forwarded'

            low_command = LowCmd(); low_command.crc = 0x12345678
            end = time.monotonic() + 4
            while time.monotonic() < end and not low_commands:
                low_command_pub.publish(low_command)
                rclpy.spin_once(node, timeout_sec=0.1)
            assert low_commands and low_commands[-1].crc == low_command.crc, '/go2/low_cmd was not forwarded'
            print(json.dumps({'result':'PASS','domain':91,'interface':'lo','topics':sorted(samples),'sensor_topics':sorted(sensor_samples),'joint_count':12,'tf':'odom -> base_link -> imu','control_bridge':True,'command_inputs':['/cmd_vel','/go2/sport_cmd','/go2/low_cmd'],'startup_commands':0,'timeout_stop':True},indent=2))
            node.destroy_node(); rclpy.shutdown()
        finally:
            os.killpg(process.pid, signal.SIGTERM)
            try: process.wait(timeout=8)
            except subprocess.TimeoutExpired: os.killpg(process.pid, signal.SIGKILL); process.wait()
