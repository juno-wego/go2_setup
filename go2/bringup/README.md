# Go2

```bash
source ~/wego_ws/install/setup.bash
ros2 launch go2 bringup.launch.py
```

RViz를 함께 켜려면 실행 명령 뒤에 `rviz:=true`를 붙인다.

| 파일 | 내용 |
|---|---|
| `~/wego_ws/go2/bringup/config/device.yaml` | 네트워크 설정 |
| `~/wego_ws/go2/bringup/config/go2.yaml` | 상태·제어 설정 |

드라이버: `~/wego_ws/go2/driver/`

[빌드 안내](../../README.md#패키지-구조와-빌드)
