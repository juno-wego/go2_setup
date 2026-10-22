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

[pub으로 이동·정지·자세 제어](../../README.md#go2-pub-제어-준비)

`/cmd_vel` 수신이 0.5초간 끊기면 속도 0의 `Move`를 한 번 보낸다.
`timeout_use_stop_move: false`로 설정해 일반 타임아웃 정지에 `StopMove`를 사용하지 않는다.
설정 변경은 bringup 재시작 후 적용된다.
