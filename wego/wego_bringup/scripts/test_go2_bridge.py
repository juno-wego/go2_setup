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
        process = subprocess.Popen(['ros2', 'launch', 'wego_bringup', 'bringup.launch.py', 'config_file:='+f.name], stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            import rclpy
            from rclpy.qos import qos_profile_sensor_data
            from sensor_msgs.msg import Imu, JointState
            from nav_msgs.msg import Odometry
            from unitree_go.msg import LowState, SportModeState
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
            low = LowState(); low.imu_state.quaternion = [1.,0.,0.,0.]
            for i in range(12): low.motor_state[i].q = 0.01 * i
            sport = SportModeState(); sport.imu_state.quaternion = [1.,0.,0.,0.]; sport.position = [2.25,-1.,0.4]
            end = time.monotonic()+12
            while time.monotonic()<end:
                low_pub.publish(low); sport_pub.publish(sport)
                rclpy.spin_once(node, timeout_sec=0.1)
                if len(samples)==3 and buffer.can_transform('odom','imu',rclpy.time.Time()): break
            assert process.poll() is None, 'Launch exited early'
            assert set(samples)=={'/go2/imu','/go2/odom','/joint_states'}, list(samples)
            assert samples['/go2/imu'].header.frame_id=='imu'
            joints=samples['/joint_states']; assert len(joints.name)==12 and abs(joints.position[11]-.11)<1e-5
            odom=samples['/go2/odom']; assert odom.header.frame_id=='odom' and odom.child_frame_id=='base_link'
            assert abs(odom.pose.pose.position.x-2.25)<1e-5 and odom.pose.pose.position.z==0.
            assert buffer.can_transform('odom','imu',rclpy.time.Time()), 'URDF/odometry TF disconnected'
            assert 'go2_cmd_vel_bridge' not in node.get_node_names(), 'Unexpected control bridge'
            print(json.dumps({'result':'PASS','domain':91,'interface':'lo','topics':sorted(samples),'joint_count':12,'tf':'odom -> base_link -> imu','control_bridge':False},indent=2))
            node.destroy_node(); rclpy.shutdown()
        finally:
            os.killpg(process.pid, signal.SIGTERM)
            try: process.wait(timeout=8)
            except subprocess.TimeoutExpired: os.killpg(process.pid, signal.SIGKILL); process.wait()
