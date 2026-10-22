# Go2 + D435i + MID-360 통합 실행

```bash
source ~/wego_ws/install/setup.bash
ros2 launch wego bringup.launch.py
```

종료: `Ctrl+C`.

설정: `~/wego_ws/wego/config/robot.yaml`

연결 상태 확인: `ros2 run wego check_hardware`

[빌드 안내](../README.md#패키지-구조와-빌드)

D435i 컬러 포인트클라우드는 통합 실행 시 기본으로 켜진다.
장착 TF는 D435i 본체의 좌우 가운데를 Go2의 `front_camera` 위에 맞추고, 현재 저장된 값인 앞으로 1cm·위로 5cm·아래로 5°를 유지한 근삿값이다. 공식 모델의 기준점 차이(왼쪽 17.5mm)를 보정했다.
`config/robot.yaml`의 `tf.d435i`에서 보정할 수 있다.
장착 TF를 끄면 카메라 좌표계의 별도 RViz 창으로 표시한다.

MID-360 외형은 Livox 공식 MID-360S CAD를 점군 원점과 축에 맞춘 메시로 표시한다. 장착 위치는 기존 브래킷 참고값을 유지한다.
