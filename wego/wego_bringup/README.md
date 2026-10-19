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

검증한 Jetson의 두 유선 포트에는 NetworkManager 수동 주소, `never-default`, 자동 연결을 저장했다.
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

장착 TF는 `tf.publish_mounts`와 센서별 `enabled`로 선택한다.
`status: reference`는 출처가 있는 참고 장착값이며 `source`가 필요하다.
실측/보정이 끝난 센서만 `status: measured`로 기록한다. xyz는 m, rpy는 rad 단위다.
알 수 없는 장착값은 `enabled: false`, `status: unconfigured`로 둔다.

현재 MID360은 공유된 Unitree 브래킷 도면의 참고값을 적용했다.
이 도면의 부모 좌표계는 **Go2 몸통 IMU**이므로 다음과 같이 연결한다.

```text
base_link → imu          xyz = (-0.02557, 0, 0.04232) m   [고정된 Wego URDF]
imu → livox_frame        xyz = ( 0.18700, 0, 0.08030) m   rpy = (0, 13°, 0)
base_link → livox_frame  xyz = ( 0.16143, 0, 0.12262) m   [위 두 변환의 합성]
```

2026-10-19에 앉히기 전 20초와 앉힌 상태 25초의 `/go2/imu`, `/livox/imu`를 비교했다.
yaw를 0으로 고정한 추정값은 각각 roll 약 −0.41°/−0.45°, pitch 약 13.58°/13.56°였다.
장착 기준값을 적용한 중력 벡터의 차이는 두 자세 모두 약 0.7°였다.
사용자가 작은 차이면 참고값을 사용하도록 요청했으므로, 1°를 판단 기준으로 정해 0°·13°를 유지했다.
이는 IMU bias까지 제거한 정밀 보정이나 오차 상한을 뜻하지 않는다.
위치는 도면 참고값이며 실측하지 않았다. yaw는 0인 참고값으로 두고 사용자 확인을 기다린다.
측정 조건과 구간별 결과: [mid360_imu_validation.json](config/mid360_imu_validation.json).
기록 당시 Livox 가속도는 g, Go2는 m/s²였으므로 각 중력 벡터를 정규화해서 비교했다.

참고 자료:

- [Unitree 도면이 공유된 GLIM 이슈](https://github.com/koide3/glim/issues/309): 제조사 원문 페이지를 직접 확인한 자료는 아니다.
- [Go2Py xacro](https://github.com/machines-in-motion/Go2Py/blob/main/deploy/ros2_nodes/go2_description/xacro/robot.xacro): 동일한 13° 값이 있지만 해당 모델의 부모 프레임을 현재 URDF에 그대로 옮기지 않았다.
- [Livox MID-360S 공식 자료](https://www.livoxtech.com/mid-360s/downloads): 매뉴얼의 IMU 축 방향은 point-cloud 축과 같고, IMU 원점은 point-cloud 기준 `(0.011, 0.02329, -0.04412)m`다. 이 내부 오프셋을 몸체 장착 xyz에 더하지 않는다.

**D435i 장착 TF는 아직 비활성화 상태다.** Go2Py 실행 파일은 카메라를 `d455`로 표기하며
별도 보정값을 사용한다. 현재 D435i와 같은 장착/보정이라는 근거가 없다.
다른 공개 Go2+D435i 모델은 커스텀 마운트여서 현재 장착에 적용하지 않았다.
RealSense 공식 URDF의 screw frame과 `camera_link`도 서로 다르므로 두 원점을 혼용하면 안 된다.
Go2의 odom/관절/본체 IMU TF와 RealSense 내부 TF는 해당 드라이버에서 제공한다.
Livox JSON의 extrinsic_parameter는 0으로 유지하여 장착 변환이 이중 적용되지 않게 한다.
Go2가 활성화되면 참고/실측 장착을 합성 URDF에 추가하고 robot_state_publisher가 TF를 발행한다.
MID360 외형은 매뉴얼 치수의 간단한 상자이며 정밀 CAD나 충돌 모델이 아니다.
상류 Go2 소스 URDF는 변경하지 않는다. Go2 비활성화 시에만 별도 static TF 노드를 사용한다.

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

주 창: Go2와 MID360 외형, TF, MID360 포인트클라우드, D435i RGB와 depth 영상.
현재 MID360은 IMU로 확인한 참고 장착 TF를 사용하여 Go2와 같은 창에 표시한다.
LiDAR 장착 TF를 끄면 MID360은 livox_frame 기준의 별도 RViz 창에 표시한다.
이 창은 센서 원점에 동일 좌표의 `livox_frame_rviz_axes` 별칭을 만들어 좌표축을 표시한다.
카메라는 영상만 표시한다. 카메라 장착 TF와 pointcloud를 모두 켜면 합성 좌표계에서 포인트클라우드를 확인할 수 있다.
LiDAR 시각화에는 `lidar.xfer_format: 0` (PointCloud2)이 필요하다.
Go2의 실제 관절 자세에는 로봇의 /lowstate 수신이 필요하다.

로봇 연결 전 Go2와 설정된 센서 외형을 확인하는 미리보기:

```bash
ros2 launch wego_bringup view_robot.launch.py
```

미리보기는 가상 관절 상태를 사용한다. 별도 loopback ROS domain 92에서
모델을 표시하며, 실제 Go2 상태 토픽과 구분된다.
화면 설정은 `rviz/robot_sensors.rviz`와 `rviz/lidar.rviz`에 있다.
카메라 토픽 경로와 LiDAR 프레임은 robot.yaml 설정에 맞춰 실행 시 반영된다.
