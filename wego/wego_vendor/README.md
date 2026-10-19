# WeGo vendor environment

wego_vendor는 SDK 경로와 Cyclone DDS 기본 환경을 등록하는 ament_cmake 패키지다.

제조사 SDK 소스:

- `~/wego_ws/src/vendor/Livox-SDK2`: MID360 SDK
- `~/wego_ws/src/vendor/librealsense`: D435i RSUSB SDK (v2.58.4)

`vendor/COLCON_IGNORE`로 SDK 소스를 ROS 패키지 검색에서 제외한다.
SDK 라이브러리와 이 환경 패키지의 설치 경로는 `~/wego_ws/install/wego_vendor`다.
SDK 빌드 캐시는 `~/wego_ws/build`에 생성한다.

```bash
source ~/wego_ws/install/setup.bash
```

위 명령으로 SDK 라이브러리·CMake 검색 경로와 DDS 기본 환경이 설정된다.
SDK 자체의 재빌드:

```bash
bash ~/wego_ws/src/wego/wego_bringup/scripts/build_livox_sdk.sh
bash ~/wego_ws/src/wego/wego_bringup/scripts/build_realsense_sdk.sh
```

고정 버전: `../wego_bringup/dependencies.lock.json`
