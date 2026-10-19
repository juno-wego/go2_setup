# Go2 + MID360 + D435i bringup

Go2는 Wego-Robot-Engeering-Team/go2의 humble 브랜치와 해당 저장소가 고정한
Unitree ROS 2 메시지를 사용한다. Livox 및 RealSense는 각 제조사의 드라이버를 사용한다.

```bash
source ~/wego_ws/install/setup.bash
ros2 launch wego_bringup bringup.launch.py
```

설정: `~/wego_ws/src/wego/wego_bringup/config/robot.yaml`.
Go2는 기본적으로 상태 수신만 활성화한다. 카메라와 LiDAR 드라이버도 함께 실행한다. 로봇을 일으키거나 이동시키는 명령을 보내지 않는다.

```bash
# 개별 장치를 임시로 제외하거나 RViz를 켤 수 있다.
ros2 launch wego_bringup bringup.launch.py enable_lidar:=false enable_camera:=false
ros2 launch wego_bringup bringup.launch.py rviz:=true
ros2 run wego_bringup check_hardware --duration 10
```

현재 확인된 포트와 주소는 다음과 같다.
라이다 검색 응답의 장치 타입은 35이며 Livox SDK에서 `Mid360s`로 식별하므로
`robot.yaml`의 `lidar.model`에 해당 타입을 설정했다. 일반 MID360은 `MID360`을 사용한다.

| 장치 | Jetson 연결 포트 / 인터페이스 | Jetson IPv4 | 장치 IPv4 |
|---|---|---|---|
| Go2 | 내장 LAN / `enP8p1s0` | `192.168.123.99/24` | `192.168.123.161` |
| MID360 | ASIX USB LAN / `enx00181af29c25` | `192.168.1.5/24` | `192.168.1.177` |
| D435i | USB, 현재 USB 2 연결 | 해당 없음 | 해당 없음 |

검증한 Jetson의 두 유선 포트에는 NetworkManager 수동 주소와 `never-default`를 저장했다.
다른 Jetson에서는 해당 포트에 주소를 별도로 설정한다. Wi-Fi 기본 경로를 유지한다.
robot.yaml의 Go2 인터페이스와 로봇 IP, LiDAR IP/host_ip는 위 배선과 맞춰져 있다.
LiDAR host_ip는 ASIX 인터페이스에 할당되어 있어야 한다.

주소가 누락되었을 때 사용하는 임시 복구 명령:

```bash
sudo python3 ~/wego_ws/src/wego/wego_bringup/scripts/configure_network.py
```

기본값은 위의 서로 다른 Go2/MID360 포트를 사용한다.
`--go2-interface`, `--lidar-interface`, `--go2-address`, `--lidar-address`로 변경할 수 있다.
이 도구는 주소를 임시 추가하며 NetworkManager의 영구 설정은 변경하지 않는다.
두 장치를 같은 LAN 포트/스위치에 연결한 배선에서는 명시적으로
`--interface enP8p1s0`를 지정하면 두 주소를 해당 포트에 추가한다.
RealSense는 USB 3 데이터 케이블로 연결하면 더 높은 지원 프로파일을 사용할 수 있다.

장착 TF는 실측 전까지 비활성화한다. `tf.mid360` 및 `tf.d435i`에 xyz(m), rpy(rad)를
입력하고 `tf.calibrated: true`, `tf.publish_mounts: true`로 설정한다.
기본 프레임은 base_link → livox_frame 및 base_link → camera_link이다.
Go2의 odom/관절/본체 IMU TF와 RealSense 내부 TF는 해당 드라이버에서 제공한다.
MID360 내부 IMU와 LiDAR 원점의 차이는 장착 TF와 별도로 취급해야 한다.
Livox JSON의 extrinsic_parameter는 0으로 유지하여 장착 변환이 이중 적용되지 않게 한다.

주요 토픽:

| 장치 | 토픽 |
|---|---|
| Go2 | /go2/odom, /go2/imu, /joint_states, /go2/battery_state |
| MID360 | /livox/lidar, /livox/imu |
| D435i | /camera/camera/color/image_raw, /camera/camera/depth/image_rect_raw, /camera/camera/imu |

`lidar.xfer_format: 0`은 PointCloud2, `1`은 Livox CustomMsg를 선택한다.
센서 연결 및 데이터 수신은 `check_hardware` 결과로 확인한다.

빌드:

```bash
~/wego_ws/src/wego/wego_bringup/scripts/build.sh
```

Jetson의 기본 커널은 `CONFIG_HID_SENSOR_HUB`가 비활성화되어 있다.
D435i IMU를 위해 librealsense v2.58.4를 RSUSB 방식으로 빌드하며,
`install/setup.bash`를 불러오면 wego_vendor 환경 훅이 워크스페이스의 SDK를 우선 사용하도록 설정한다. 커널 패치는 적용하지 않는다.
현재 USB 2 연결에 맞춰 depth=480x270@15, color=640x480@15로 설정했다.
D435i IMU 데이터는 수신되지만 SDK에서 IMU 보정을 읽지 못해 기본 intrinsic/extrinsic을 사용한다는 경고가 확인됐다.
USB 3로 연결한 뒤에는 robot.yaml에서 원하는 지원 프로파일로 변경할 수 있다.
SDK 재빌드: `bash ~/wego_ws/src/wego/wego_bringup/scripts/build_realsense_sdk.sh`.
공식 Jetson 설치 안내: https://github.com/realsenseai/librealsense/blob/v2.58.4/doc/installation_jetson.md

검증한 Jetson의 AVerMedia BSP는 L4T 36.4.4 기반이다. 일반 apt upgrade에서 올라간 36.4.7은
jetson-orin-d115 보드를 지원하지 않아 NVIDIA L4T 패키지를 36.4.4로 복구하고
원본 BSP의 Image/모듈/보드 DTB를 복원했다. nvidia-l4t-* 패키지는 hold 상태다.
보드 제조사 BSP 업데이트 절차 없이 해당 hold를 해제하지 않는다.
이 저장소에는 부팅 복구 파일을 포함하지 않는다.

Go2의 DDS 수신은 `network_interface`와 `domain_id`를 사용한다.
`go2.robot_ip`는 장치 식별을 위한 참고 주소이며 DDS의 접속 대상을 지정하는 옵션은 아니다.
실측 장착값을 알 수 없다면 제조사/장착 브래킷 도면 또는 LiDAR-camera 외부 보정이 필요하다.
Go2 본체 URDF: `~/wego_ws/src/drivers/go2/go2_description/urdf/go2_description.urdf`.
RealSense의 camera_link 아래 센서/optical 프레임 변환은 카메라 드라이버가 보정값으로 제공한다.

SDK 소스는 `src/vendor`, 설치물은 `install/wego_vendor`에 모아 두었다.
일반 ROS 빌드는 설치된 SDK를 재사용한다. SDK 자체를 변경한 경우에는
`scripts/build_livox_sdk.sh` 또는 `scripts/build_realsense_sdk.sh`를 먼저 실행한다.

## RViz

Go2 상태 수신과 센서 드라이버를 실행하면서 RViz도 함께 시작한다.
Jetson 데스크톱 터미널에서 실행한다.

```bash
source ~/wego_ws/install/setup.bash
ros2 launch wego_bringup bringup.launch.py rviz:=true
```

주 창: Go2 RobotModel, TF, D435i RGB와 depth 영상.
장착 TF가 미보정 상태이면 MID360은 livox_frame 기준의 별도 RViz 창에 표시한다.
이 창은 센서 원점에 동일 좌표의 `livox_frame_rviz_axes` 별칭을 만들어 좌표축을 표시한다.
Go2와 센서 사이의 장착 변환은 실측값을 입력한 뒤 활성화한다.
실측 장착 TF를 활성화하면 주 창에서 Go2와 MID360 포인트클라우드를 함께 표시한다.
카메라 pointcloud도 켜면 보정된 좌표계에서 선택적으로 확인할 수 있다.
LiDAR 시각화에는 `lidar.xfer_format: 0` (PointCloud2)이 필요하다.
Go2의 실제 관절 자세에는 로봇의 /lowstate 수신이 필요하다.

로봇 연결 전 Go2 URDF 형태를 확인하는 미리보기:

```bash
ros2 launch wego_bringup view_robot.launch.py
```

미리보기는 가상 관절 상태를 사용한다. 별도 loopback ROS domain 92에서
모델을 표시하며, 실제 Go2 상태 토픽과 구분된다.
화면 설정은 `rviz/robot_sensors.rviz`와 `rviz/lidar.rviz`에 있다.
카메라 토픽 경로와 LiDAR 프레임은 robot.yaml 설정에 맞춰 실행 시 반영된다.
