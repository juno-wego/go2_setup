# Go2 + D435i + MID-360 통합 실행

```bash
source ~/wego_ws/install/setup.bash
ros2 launch wego bringup.launch.py
```

종료: `Ctrl+C`.

설정: `~/wego_ws/wego/config/robot.yaml`

연결 상태 확인: `ros2 run wego check_hardware`

[빌드 안내](../README.md#패키지-구조와-빌드)
