# Go2 + D435i + MID-360 사용 안내

[PDF 매뉴얼](docs/WeGo_고객_매뉴얼.pdf)

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
| MID-360 | LAN (`mid360`) | `192.168.1.5/24` | `192.168.1.120` |
| D435i | USB | — | — |

D435i 영상 설정: 컬러 640 × 480, 거리 480 × 270. 각각 초당 15장.

현재 D435i 일련번호: `261722076686`.
카메라를 교체하면 `~/wego_ws/wego/config/robot.yaml`의 `camera.serial_no`를 맞춘다.

D435i 포인트클라우드는 통합 실행 시 Go2·MID-360과 같은 RViz 화면에 표시한다. MID-360 외형은 연결된 장비에 맞는 Livox 공식 MID-360S CAD 모델로 표시한다.

### 현재 LAN 포트 설정

| 용도 | 인터페이스 이름 | MAC 주소 |
|---|---|---|
| Go2 — 내장 LAN | `go2` | `74:25:54:00:0f:8a` |
| MID-360 — USB LAN | `mid360` | `00:18:1a:f2:99:58` |

캐리어보드나 USB LAN을 교체하면 MAC 주소가 달라질 수 있다.
`Network interface 'go2' does not exist` 오류가 나면
`/etc/systemd/network/10-go2.link`, `/etc/systemd/network/10-mid360.link`의
MAC 주소와 NetworkManager의 해당 연결 조건을 확인한다.
센서용 LAN에는 위의 고정 IP를 사용하며 기본 게이트웨이는 지정하지 않는다.


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
| `/camera/camera/depth/color/points` | `sensor_msgs/msg/PointCloud2` | 컬러 3차원 측정점 (통합 실행 시 켜짐) |

### Go2 제어 입력

| 토픽 | 메시지 형식 | 내용 |
|---|---|---|
| `/cmd_vel` | `geometry_msgs/msg/Twist` | 이동 속도 [m/s]·회전 속도 [rad/s] |
| `/go2/sport_cmd` | `go2_interface/msg/SportCmd` | 자세·동작 명령 |
| `/go2/low_cmd` | `unitree_go/msg/LowCmd` | 관절·모터 직접 제어 명령 |

`/cmd_vel` 수신이 0.5초간 중단되면 브리지가 속도 0의 `Move`를 한 번 보낸다.
일반 정지에 `StopMove`를 사용하지 않도록 설정했다.

## 좌표계

| 기준 → 장치 | 위치 (x, y, z) [m] | 회전 (X, Y, Z축) [°] | 상태 |
|---|---|---|---|
| `base_link → imu` | `(-0.02557, 0, 0.04232)` | `(0, 0, 0)` | 고정값 |
| `imu → livox_frame` | `(0.187, 0, 0.0803)` | `(0, 13, 0)` | 장착 참고값, Z축 회전각 미확인 |
| `front_camera → camera_link` | `(0.01, 0.0175, 0.05)` | `(0, 5, 0)` | 현재 설정값, 실측 미확인 |

D435i 본체의 좌우 가운데를 Go2 전면 카메라 위에 맞추고, 현재 설정은 전면 카메라보다 앞으로 1cm·위로 5cm·아래로 5°이다.
공식 모델의 `camera_link`는 본체의 좌우 가운데보다 왼쪽으로 17.5mm에 있어 이 차이를 보정했다.
D435i 위치와 기울기는 사용자 설명에 따른 근삿값이다. MID-360 위치는 기존 브래킷 참고값이며, IMU 비교로 확인한 것은 기울기다. 센서 위치는 실측 보정이 필요하다.

## Go2 pub 제어 준비

현재 Jetson은 새 터미널을 열면 ROS 2와 `wego_ws`를 자동으로 불러온다.
통합 bringup을 실행해 둔 상태라면 추가 준비 명령 없이 아래 `ros2 topic pub` 명령을 실행하면 된다.
평평한 바닥에서 주변 공간을 확보하고, 앱에 경고가 없는지 확인한다.
조종기로 즉시 정지할 수 있는 상태에서 명령을 하나씩 실행한다.

자동 로딩이 설정되지 않은 환경에서만 다음 한 줄을 먼저 실행한다.

```bash
source ~/wego_ws/install/setup.bash
```

### 이동 축과 일반 정지

| 입력 | 양수 방향 | 음수 방향 | 단위 |
|---|---|---|---|
| `linear.x` | 로봇 앞 | 로봇 뒤 | m/s |
| `linear.y` | 로봇 왼쪽 | 로봇 오른쪽 | m/s |
| `angular.z` | 왼쪽 회전 | 오른쪽 회전 | rad/s |

일반 정지: 모든 속도를 0으로 보낸다.

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  '{linear: {x: 0.0, y: 0.0}, angular: {z: 0.0}}'
```

이동 명령의 발행을 끝내면 0.5초 뒤 브리지가 속도 0을 한 번 보낸다.
입력이 끊기는 것 자체가 속도 0 명령은 아니므로 자동 정지는 유지한다.
명령 처리와 통신 지연 때문에 실제 정지 시점은 달라질 수 있다.
`/go2/sport_cmd`의 `stop_move`는 별도의 `StopMove` 요청이며, 현재 장비에서 멈출 때 모드가 바뀌는 증상이 있어 일반 정지 예제에서는 사용하지 않는다.

설정: `~/wego_ws/go2/bringup/config/go2.yaml`의 `cmd_timeout: 0.5`,
`stop_on_timeout: true`, `timeout_use_stop_move: false`.
설정을 바꾸면 bringup을 `Ctrl+C`로 종료한 뒤 다시 실행해야 적용된다.
bringup 시작 시 자동 일어서기·보행 모드 전환은 꺼져 있다.

## Go2 이동 명령

다음 명령은 20Hz로 20번, 약 1초 동안 입력을 발행한다.
실제 이동 시간과 거리는 보장하지 않는다. 생략한 속도 성분은 0이다.

### 앞으로 — 0.02m/s

```bash
ros2 topic pub --rate 20 --times 20 \
  /cmd_vel geometry_msgs/msg/Twist '{linear: {x: 0.02}}'
```

### 뒤로 — 0.02m/s

```bash
ros2 topic pub --rate 20 --times 20 \
  /cmd_vel geometry_msgs/msg/Twist '{linear: {x: -0.02}}'
```

### 왼쪽 — 0.02m/s

```bash
ros2 topic pub --rate 20 --times 20 \
  /cmd_vel geometry_msgs/msg/Twist '{linear: {y: 0.02}}'
```

### 오른쪽 — 0.02m/s

```bash
ros2 topic pub --rate 20 --times 20 \
  /cmd_vel geometry_msgs/msg/Twist '{linear: {y: -0.02}}'
```

### 제자리 왼쪽 회전 — 0.05rad/s

```bash
ros2 topic pub --rate 20 --times 20 \
  /cmd_vel geometry_msgs/msg/Twist '{angular: {z: 0.05}}'
```

### 제자리 오른쪽 회전 — 0.05rad/s

```bash
ros2 topic pub --rate 20 --times 20 \
  /cmd_vel geometry_msgs/msg/Twist '{angular: {z: -0.05}}'
```

발행 주기를 생략하면 기본값은 1Hz라서 현재 0.5초 타임아웃보다 느리다.
이동 입력에는 `--rate 20`을 유지한다. 다른 이동 명령 발행기와 동시에 실행하지 않는다.

## Go2 자세 명령

각 명령은 실제 자세를 바꾼다. 다리 동작 범위 밖에서 한 가지씩 실행하고 결과를 확인한다.

### 일어서기

```bash
ros2 topic pub --once /go2/sport_cmd go2_interface/msg/SportCmd \
  '{command: stand_up}'
```

### 균형 서기

```bash
ros2 topic pub --once /go2/sport_cmd go2_interface/msg/SportCmd \
  '{command: balance_stand}'
```

### 엎드리기

```bash
ros2 topic pub --once /go2/sport_cmd go2_interface/msg/SportCmd \
  '{command: stand_down}'
```

### 몸체 기울이기 — pitch +1° 요청

균형 서기 상태에서 작은 각도부터 사용한다. `roll`, `pitch`, `yaw`는 rad 단위이며,
1°는 약 0.0174533rad이다. `Twist.angular.z`의 회전 속도와 구분한다.

```bash
ros2 topic pub --once /go2/sport_cmd go2_interface/msg/SportCmd \
  '{command: euler, roll: 0.0, pitch: 0.0174533, yaw: 0.0}'
```

### 몸체 기울기 원위치

```bash
ros2 topic pub --once /go2/sport_cmd go2_interface/msg/SportCmd \
  '{command: euler, roll: 0.0, pitch: 0.0, yaw: 0.0}'
```

메시지와 API 변환은 로봇과 분리된 환경에서 확인했다. 자세 명령의 실제 동작은 현재 장비에서 확인 전이며, 펌웨어와 현재 제어 모드에 따라 지원 여부가 달라질 수 있다.
참고: [Unitree 공식 SportClient API](https://github.com/unitreerobotics/unitree_sdk2/blob/main/include/unitree/robot/go2/sport/sport_client.hpp).
