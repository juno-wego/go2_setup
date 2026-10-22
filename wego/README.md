# Go2 + D435i + MID-360 통합 실행

```bash
source ~/wego_ws/install/setup.bash
ros2 launch wego bringup.launch.py
```

종료: `Ctrl+C`.

설정: `~/wego_ws/wego/config/robot.yaml`

연결 상태 확인: `ros2 run wego check_hardware`

[빌드 안내](../README.md#패키지-구조와-빌드)

D435i 컬러 점군은 기본으로 켜진다.
장착 TF는 `config/robot.yaml`에서 설정한다.
장착 TF를 끄면 카메라 점군을 별도 RViz 창에 표시한다.

MID-360 외형은 Livox 공식 MID-360S 모델을 사용한다.
