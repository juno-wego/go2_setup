# Go2 + Livox + RealSense setup

Jetson에서 검증한 Go2, Livox MID360 계열, RealSense D435i의 ROS 2 Humble 통합 구성이다.
이 저장소를 `~/wego_ws/src` 위치에 내려받아 사용한다.

```text
wego_ws/
├── src/                         # 이 저장소
│   ├── drivers/
│   │   ├── go2/                 # Wego humble + Unitree 서브모듈
│   │   └── livox_ros_driver2/
│   ├── vendor/
│   │   ├── Livox-SDK2/
│   │   └── librealsense/
│   └── wego/
│       ├── wego_bringup/         # 통합 launch, 설정, RViz, 빌드 도구
│       └── wego_vendor/          # SDK 및 DDS 환경 설정
├── build/                       # 빌드 후 생성
├── install/                     # 빌드 후 생성
└── log/                         # 빌드 후 생성
```

## 소스 다운로드

새 워크스페이스에서 실행한다. 기존 `~/wego_ws/src`가 있으면 다른 워크스페이스 경로를 사용한다.

```bash
mkdir -p ~/wego_ws
git clone --recurse-submodules https://github.com/juno-wego/go2_setup.git ~/wego_ws/src
```

외부 드라이버·SDK는 Jetson에서 검증한 커밋에 고정한 서브모듈이다.
GitHub의 **Download ZIP** 대신 위 명령으로 내려받는다.
이미 일반 clone을 했다면 다음 명령으로 외부 소스를 받는다.

```bash
git -C ~/wego_ws/src submodule update --init --recursive
```

고정 버전 목록: [dependencies.lock.json](wego/wego_bringup/dependencies.lock.json).
각 외부 소스의 라이선스는 해당 서브모듈을 따른다.

## 빌드

Ubuntu 22.04와 ROS 2 Humble이 설치된 환경에서 사용한다.
검증 환경은 JetPack 6.2.1 / L4T 36.4.4, RealSense ROS 4.58.4 및 librealsense 2.58.4이다.
ROS 설치, 제조사 BSP 플래싱, OS 부팅 파일은 이 저장소에 포함하지 않는다.

필요한 도구와 ROS 패키지를 설치한다. ROS 2 apt 저장소가 설정되어 있어야 한다.

```bash
sudo apt update
sudo apt install -y build-essential cmake pkg-config git \
  libusb-1.0-0-dev libudev-dev libssl-dev libpcl-dev libapr1-dev \
  python3-colcon-common-extensions python3-yaml python3-pytest \
  ros-humble-ros-base ros-humble-ament-cmake-auto \
  ros-humble-rosidl-default-generators ros-humble-pcl-conversions \
  ros-humble-rmw-cyclonedds-cpp ros-humble-rviz2 \
  ros-humble-robot-state-publisher ros-humble-joint-state-publisher \
  ros-humble-xacro ros-humble-tf2-ros ros-humble-realsense2-camera

bash ~/wego_ws/src/wego/wego_bringup/scripts/build.sh
```

첫 빌드는 Livox SDK와 RSUSB 방식의 librealsense도 컴파일하므로 시간이 걸린다.
이후에는 `install/wego_vendor`에 설치한 SDK를 재사용한다.
D435i의 USB 접근 권한을 위해 공식 SDK의 udev 규칙도 적용한다.

```bash
sudo bash ~/wego_ws/src/vendor/librealsense/scripts/setup_udev_rules.sh
```

규칙 적용 후 카메라 USB를 다시 연결한다.

## 실행

Jetson 데스크톱 터미널에서 실행한다.

```bash
source ~/wego_ws/install/setup.bash
ros2 launch wego_bringup bringup.launch.py rviz:=true
```

Go2 모델과 실제 관절 상태, D435i RGB·깊이 영상, Livox 포인트클라우드를 표시한다.
기본 설정에서는 Go2 상태를 수신하며 이동 명령을 보내지 않는다.
장착 TF를 실측하기 전에는 라이다를 센서 좌표계의 별도 RViz 창에 표시한다.

로봇 연결 없이 URDF 형태만 확인하려면:

```bash
ros2 launch wego_bringup view_robot.launch.py
```

데이터 수신 확인:

```bash
ros2 run wego_bringup check_hardware --duration 10
```

## 장치 설정

설정 파일: [robot.yaml](wego/wego_bringup/config/robot.yaml).
포트 이름, IP, 카메라 일련번호는 실제 연결에 맞춰 변경한다.

| 장치 | 현재 Jetson 인터페이스 | Jetson IP | 장치 IP |
|---|---|---|---|
| Go2 | `enP8p1s0` | `192.168.123.99/24` | `192.168.123.161` |
| Livox | `enx00181af29c25` | `192.168.1.5/24` | `192.168.1.177` |
| D435i | USB | — | — |

현재 라이다의 검색 응답은 장치 타입 35이므로 `lidar.model: Mid360s`를 사용한다.
일반 MID360은 `lidar.model: MID360`으로 설정한다.
다른 Jetson에서 센서용 IPv4 주소를 임시 추가하려면:

```bash
sudo python3 ~/wego_ws/src/wego/wego_bringup/scripts/configure_network.py
```

임시 주소는 재부팅 후 사라진다. 상시 사용하려면 각 LAN 연결에 수동 IPv4 주소를 저장한다.
Wi-Fi로 인터넷을 사용한다면 센서용 LAN에는 기본 게이트웨이를 지정하지 않는다.

`tf.mid360`, `tf.d435i`의 실측 xyz(m)·rpy(rad)를 입력하고
`tf.calibrated`, `tf.publish_mounts`를 모두 `true`로 설정하면 장착 TF를 활성화한다.
현재 D435i는 USB 2 프로파일로 설정되어 있으며 IMU 기본 보정값 사용 경고가 확인됐다.

상세 토픽·TF·SDK 안내: [wego_bringup README](wego/wego_bringup/README.md).

## 확인한 내용

Jetson에서 Go2 관절·IMU·odom, Livox 포인트클라우드·IMU,
D435i RGB·깊이·IMU의 실제 수신과 RViz 표시를 확인했다.
설정 및 launch 격리 테스트 10개가 통과했다.

```bash
source ~/wego_ws/install/setup.bash
python3 -m pytest -q ~/wego_ws/src/wego/wego_bringup/test
```
