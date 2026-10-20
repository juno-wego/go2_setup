# D435i

```bash
source ~/wego_ws/install/setup.bash
ros2 launch d435i bringup.launch.py
```

설정: `~/wego_ws/d435i/config/device.yaml`

`serial_no`는 카메라 시리얼 번호다. 비워 두면 연결된 카메라를 사용한다.

| 항목 | 위치 |
|---|---|
| ROS 드라이버 | `/opt/ros/humble/share/realsense2_camera/` |
| 카메라 모델 파일 | `/opt/ros/humble/share/realsense2_description/` |
| SDK 소스 | `~/wego_ws/d435i/vendor/librealsense/` |

[빌드 안내](../README.md#패키지-구조와-빌드)
