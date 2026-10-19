# Go2 + D435i + MID-360 통합 실행

워크스페이스 루트에서 실행한다.

```bash
source install/setup.bash
ros2 launch wego bringup.launch.py
```

종료: `Ctrl+C`.

이 패키지는 `go2`, `mid360`, `d435i`의 launch를 조합한다.
장치 드라이버 설정·SDK·Go2 내장 센서 처리는 각각의 장치 패키지가 담당한다.
통합 설정은 `config/robot.yaml`, 장착 TF와 통합 시각화는 이 패키지가 담당한다.

```bash
ros2 launch wego bringup.launch.py config_file:=/path/to/robot.yaml rviz:=false
ros2 run wego check_hardware
```

프로파일에서 생략한 장치는 실행하지 않는다. 예를 들어 아래 파일은 카메라만 실행한다.
Go2 네트워크 인터페이스나 LiDAR 주소가 필요하지 않다.

```yaml
camera:
  enabled: true
  serial_no: ''
```

Go2를 함께 실행하면 센서와 RViz도 동일한 DDS 설정을 사용한다.
센서만 실행하면 호출 환경의 DDS 설정을 사용한다.
센서 내부 TF는 드라이버가, 로봇과 센서 사이 장착 TF는 통합 구성이 소유한다.

전체 빌드는 저장소 루트의 `build.sh`를 사용한다.

- [운용 안내](../README.md#실행)
- [장치 제원](../README.md#장치-제원)
- [토픽 인터페이스](../README.md#토픽-인터페이스)
