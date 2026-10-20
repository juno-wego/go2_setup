# Go2 + D435i + MID-360 사용 안내

## 로그인

ID : `nvidia`

비밀번호 : `nvidia`

## 실행

Jetson에서 Go2, MID-360, D435i를 함께 실행한다.

```bash
source ~/wego_ws/install/setup.bash
ros2 launch wego bringup.launch.py
```

종료: `Ctrl+C`.

장치별 단독 실행:

```bash
ros2 launch go2 bringup.launch.py
ros2 launch mid360 bringup.launch.py
ros2 launch d435i bringup.launch.py
```

설정: `~/wego_ws/wego/config/robot.yaml`

## 패키지 구조와 빌드

```text
~/wego_ws/
├── go2/
│   ├── bringup/
│   └── driver/
├── mid360/
│   ├── bringup/
│   │   └── vendor/Livox-SDK2/
│   └── driver/
├── d435i/
│   └── vendor/librealsense/
└── wego/
```

Jetson에서 소스 수정 후 빌드:

```bash
cd ~/wego_ws
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

## 연결

| 장치 | 연결 | Jetson IP | 장치 IP |
|---|---|---|---|
| Go2 | LAN (`go2`) | `192.168.123.99/24` | `192.168.123.161` |
| MID-360 | LAN (`mid360`) | `192.168.1.5/24` | `192.168.1.177` |
| D435i | USB | — | — |

D435i 영상 설정: 컬러 640 × 480, 거리 480 × 270. 각각 초당 15장.

## 장치 사양

### [Unitree Go2](https://www.unitree.com/go2/)

| 항목 | 사양 |
|---|---|
| 크기 | 서 있을 때 700 × 310 × 400 mm, 엎드렸을 때 760 × 310 × 200 mm |
| 무게 | 배터리 포함 약 15 kg |
| 관절 | 12개 |
| 전압 | 28–33.6 V |
| 배터리 | 8,000 / 15,000 mAh |
| 사용 시간 | 약 1–4시간 |
| 속도 | AIR 2.5 m/s, PRO 3.5 m/s, X·EDU 3.7 m/s |
| 실을 수 있는 무게 | AIR 약 7 kg, PRO·X·EDU 약 8 kg |

### [RealSense D435i](https://www.realsenseai.com/download/21345/?tmstv=1770190765)

| 항목 | 사양 |
|---|---|
| 크기 / 무게 | 90 × 25 × 25 mm / 약 75 g |
| 권장 거리 | 0.3–3 m |
| 거리 영상 | 1280 × 720 (초당 30장), 848 × 480 (초당 90장) |
| 컬러 영상 | 1920 × 1080 (초당 30장) |
| 촬영 범위 (가로 × 세로) | 거리 87° × 58°, 컬러 69° × 42° |
| 움직임 센서 | 가속도 3축·회전 속도 3축 |
| 연결 / 전원 | USB-C, USB 3.1 Gen 1 / 5 V |

### [Livox MID-360](https://www.livoxtech.com/mid-360/specs)

| 항목 | 사양 |
|---|---|
| 크기 / 무게 | 65 × 65 × 60 mm / 265 g |
| 측정 거리 | 40 m (물체의 빛 반사율 10%, 주변 밝기 100,000 lx) |
| 측정 범위 | 가로 360°, 세로 −7°~52° |
| 최소 측정 거리 | 0.1 m |
| 측정점 수 | 초당 200,000개 |
| 데이터 출력 | 초당 10회 |
| 움직임 센서 | 가속도 3축·회전 속도 3축 |
| 연결 | 유선 LAN (100 Mbps) |
| 전원 / 소비전력 | 9–27 V DC / 6.5 W |
| 동작 온도 / 보호 등급 | −20–55°C / IP67 |

## 토픽 목록

### Go2 상태

| 토픽 | 메시지 형식 | 내용 |
|---|---|---|
| `/go2/odom` | `nav_msgs/msg/Odometry` | 위치·속도 |
| `/go2/imu` | `sensor_msgs/msg/Imu` | 본체 가속도·회전 속도 |
| `/joint_states` | `sensor_msgs/msg/JointState` | 12개 관절의 상태 |
| `/go2/foot_force` | `std_msgs/msg/Int16MultiArray` | 발 힘 센서 원본값 |
| `/go2/battery_state` | `go2_interface/msg/Go2BatteryState` | 전압·전류·잔량·충전 상태 |
| `/go2/sport_state` | `unitree_go/msg/SportModeState` | 로봇 동작 상태 |
| `/go2/low_state` | `unitree_go/msg/LowState` | 관절·모터·배터리 상태 |
| `/go2/wireless_controller` | `unitree_go/msg/WirelessController` | 조종기 입력 |
| `/go2/uwb_state` | `unitree_go/msg/UwbState` | 무선 거리·방향 센서(UWB) 상태 |

### Go2 내장 센서

| 토픽 | 메시지 형식 | 내용 |
|---|---|---|
| `/go2/lidar` | `sensor_msgs/msg/PointCloud2` | 내장 LiDAR의 3차원 측정점 |
| `/go2/lidar/imu` | `sensor_msgs/msg/Imu` | 내장 LiDAR의 가속도·회전 속도 |
| `/go2/lidar/state` | `unitree_go/msg/LidarState` | 내장 LiDAR 상태 |
| `/go2/camera/image_raw` | `sensor_msgs/msg/Image` | 전면 영상, 1920 × 1080 |
| `/go2/camera/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | JPEG 압축 영상 |

### MID-360

| 토픽 | 메시지 형식 | 내용 |
|---|---|---|
| `/livox/lidar` | `sensor_msgs/msg/PointCloud2` | 3차원 측정점, 초당 10회 |
| `/livox/imu` | `sensor_msgs/msg/Imu` | 가속도 [g]·회전 속도 [rad/s] |

### D435i

| 토픽 | 메시지 형식 | 내용 |
|---|---|---|
| `/camera/camera/color/image_raw` | `sensor_msgs/msg/Image` | 컬러 영상 |
| `/camera/camera/depth/image_rect_raw` | `sensor_msgs/msg/Image` | 거리 영상 |
| `/camera/camera/aligned_depth_to_color/image_raw` | `sensor_msgs/msg/Image` | 컬러 영상에 위치를 맞춘 거리 영상 |
| `/camera/camera/color/camera_info` | `sensor_msgs/msg/CameraInfo` | 컬러 카메라 보정값 |
| `/camera/camera/depth/camera_info` | `sensor_msgs/msg/CameraInfo` | 거리 카메라 보정값 |
| `/camera/camera/aligned_depth_to_color/camera_info` | `sensor_msgs/msg/CameraInfo` | 거리 영상 보정값 (컬러 기준) |
| `/camera/camera/gyro/sample` | `sensor_msgs/msg/Imu` | 회전 속도 |
| `/camera/camera/accel/sample` | `sensor_msgs/msg/Imu` | 가속도 |
| `/camera/camera/imu` | `sensor_msgs/msg/Imu` | 회전 속도·가속도를 묶은 값 |
| `/camera/camera/depth/color/points` | `sensor_msgs/msg/PointCloud2` | 3차원 측정점 (기본 꺼짐) |

### Go2 제어 입력

| 토픽 | 메시지 형식 | 내용 |
|---|---|---|
| `/cmd_vel` | `geometry_msgs/msg/Twist` | 이동 속도 [m/s]·회전 속도 [rad/s] |
| `/go2/sport_cmd` | `go2_interface/msg/SportCmd` | 자세·동작 명령 |
| `/go2/low_cmd` | `unitree_go/msg/LowCmd` | 관절·모터 직접 제어 명령 |

`/cmd_vel` 수신이 0.5초간 중단되면 정지한다.

## 좌표계

| 기준 → 장치 | 위치 (x, y, z) [m] | 회전 (X, Y, Z축) [°] | 상태 |
|---|---|---|---|
| `base_link → imu` | `(-0.02557, 0, 0.04232)` | `(0, 0, 0)` | 고정값 |
| `imu → livox_frame` | `(0.187, 0, 0.0803)` | `(0, 13, 0)` | 장착 참고값, Z축 회전각 미확인 |
