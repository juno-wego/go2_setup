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

`/cmd_vel` 입력이 0.5초간 없으면 속도 0 명령을 보낸다.
