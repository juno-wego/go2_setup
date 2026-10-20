# Go2 + D435i + MID-360 운용 안내


- [로그인](#로그인)
- [실행](#실행)
- [패키지 구조와 빌드](#패키지-구조와-빌드)
- [연결](#연결)
- [장치 제원](#장치-제원)
- [토픽 인터페이스](#토픽-인터페이스)
- [좌표계](#좌표계)


## 로그인

ID : `nvidia`

비밀번호 : `nvidia`

## 실행

Jetson 터미널에서 실행한다.

```bash
source ~/wego_ws/install/setup.bash
ros2 launch wego bringup.launch.py
```

RViz에서 Go2 관절·내장 LiDAR·전면 영상, MID-360 포인트클라우드, D435i RGB·깊이 영상을 확인한다.
주행·자세 명령은 제어 토픽으로 전달한다. 종료는 실행 터미널에서 `Ctrl+C`.

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

D435i 영상: RGB 640 × 480 @ 15 fps, 깊이 480 × 270 @ 15 fps.

## 장치 제원

### [Unitree Go2](https://www.unitree.com/go2/)

| 항목 | 제원 |
|---|---|
| 크기 | 기립 700 × 310 × 400 mm, 엎드림 760 × 310 × 200 mm |
| 무게 | 배터리 포함 약 15 kg |
| 관절 | 12개 |
| 전압 | 28–33.6 V |
| 배터리 | 8,000 / 15,000 mAh |
| 사용 시간 | 약 1–4시간 |
| 속도 | AIR 2.5 m/s, PRO 3.5 m/s, X·EDU 3.7 m/s |
| 적재 하중 | AIR 약 7 kg, PRO·X·EDU 약 8 kg |

### [RealSense D435i](https://www.realsenseai.com/download/21345/?tmstv=1770190765)

| 항목 | 제원 |
|---|---|
| 크기 / 무게 | 90 × 25 × 25 mm / 약 75 g |
| 깊이 측정 | 능동 스테레오, Global Shutter |
| 권장 거리 | 0.3–3 m |
| 깊이 영상 | 1280 × 720 @ 30 fps, 848 × 480 @ 90 fps |
| RGB 영상 | 1920 × 1080 @ 30 fps, Rolling Shutter |
| 시야각 (수평 × 수직) | 깊이 87° × 58°, RGB 69° × 42° |
| IMU | 6축 가속도·자이로 |
| 연결 / 전원 | USB-C, USB 3.1 Gen 1 / 5 V |

### [Livox MID-360](https://www.livoxtech.com/mid-360/specs)

| 항목 | 제원 |
|---|---|
| 크기 / 무게 | 65 × 65 × 60 mm / 265 g |
| 측정 거리 | 40 m (반사율 10%, 100 klx) |
| 시야각 | 수평 360°, 수직 −7°~52° |
| 근거리 사각 | 0.1 m |
| 점 출력 / 프레임률 | 200,000 points/s / 10 Hz |
| IMU | 6축 가속도·자이로 |
| 연결 | 100 BASE-TX Ethernet |
| 전원 / 소비전력 | 9–27 V DC / 6.5 W |
| 동작 온도 / 보호 등급 | −20–55°C / IP67 |

## 토픽 인터페이스

### Go2 상태

| 토픽 | 메시지 타입 | 내용 |
|---|---|---|
| `/go2/odom` | `nav_msgs/msg/Odometry` | 위치·속도 |
| `/go2/imu` | `sensor_msgs/msg/Imu` | 본체 IMU |
| `/joint_states` | `sensor_msgs/msg/JointState` | 12관절 상태 |
| `/go2/foot_force` | `std_msgs/msg/Int16MultiArray` | 발 힘 원시값 |
| `/go2/battery_state` | `go2_interface/msg/Go2BatteryState` | 전압·전류·잔량·충전 상태 |
| `/go2/sport_state` | `unitree_go/msg/SportModeState` | 로봇 동작 상태 |
| `/go2/low_state` | `unitree_go/msg/LowState` | 관절·모터·BMS 전체 상태 |
| `/go2/wireless_controller` | `unitree_go/msg/WirelessController` | 조종기 입력 |
| `/go2/uwb_state` | `unitree_go/msg/UwbState` | UWB 상태 |

### Go2 내장 센서

| 토픽 | 메시지 타입 | 내용 |
|---|---|---|
| `/go2/lidar` | `sensor_msgs/msg/PointCloud2` | 내장 LiDAR 포인트클라우드 |
| `/go2/lidar/imu` | `sensor_msgs/msg/Imu` | 내장 LiDAR IMU |
| `/go2/lidar/state` | `unitree_go/msg/LidarState` | 내장 LiDAR 상태 |
| `/go2/camera/image_raw` | `sensor_msgs/msg/Image` | 전면 영상, 1920 × 1080 |
| `/go2/camera/image_raw/compressed` | `sensor_msgs/msg/CompressedImage` | JPEG 영상 |

### MID-360

| 토픽 | 메시지 타입 | 내용 |
|---|---|---|
| `/livox/lidar` | `sensor_msgs/msg/PointCloud2` | 포인트클라우드, 10 Hz |
| `/livox/imu` | `sensor_msgs/msg/Imu` | 가속도 [g]·각속도 [rad/s] |

### D435i

| 토픽 | 메시지 타입 | 내용 |
|---|---|---|
| `/camera/camera/color/image_raw` | `sensor_msgs/msg/Image` | RGB 영상 |
| `/camera/camera/depth/image_rect_raw` | `sensor_msgs/msg/Image` | 깊이 영상 |
| `/camera/camera/aligned_depth_to_color/image_raw` | `sensor_msgs/msg/Image` | RGB에 정렬한 깊이 영상 |
| `/camera/camera/color/camera_info` | `sensor_msgs/msg/CameraInfo` | RGB 내부 파라미터 |
| `/camera/camera/depth/camera_info` | `sensor_msgs/msg/CameraInfo` | 깊이 내부 파라미터 |
| `/camera/camera/aligned_depth_to_color/camera_info` | `sensor_msgs/msg/CameraInfo` | 정렬 깊이 내부 파라미터 |
| `/camera/camera/gyro/sample` | `sensor_msgs/msg/Imu` | 자이로 |
| `/camera/camera/accel/sample` | `sensor_msgs/msg/Imu` | 가속도 |
| `/camera/camera/imu` | `sensor_msgs/msg/Imu` | 결합 IMU |
| `/camera/camera/depth/color/points` | `sensor_msgs/msg/PointCloud2` | 포인트클라우드 (기본 비활성) |

### Go2 제어 입력

| 토픽 | 메시지 타입 | 내용 |
|---|---|---|
| `/cmd_vel` | `geometry_msgs/msg/Twist` | 이동 속도 [m/s]·회전 속도 [rad/s] |
| `/go2/sport_cmd` | `go2_interface/msg/SportCmd` | 자세·동작 명령 |
| `/go2/low_cmd` | `unitree_go/msg/LowCmd` | 저수준 명령 |

`/cmd_vel` 수신이 0.5초간 중단되면 정지한다.

## 좌표계

| 변환 | xyz [m] | rpy [°] | 상태 |
|---|---|---|---|
| `base_link → imu` | `(-0.02557, 0, 0.04232)` | `(0, 0, 0)` | 고정값 |
| `imu → livox_frame` | `(0.187, 0, 0.0803)` | `(0, 13, 0)` | 장착 참고값, yaw 미확인 |
