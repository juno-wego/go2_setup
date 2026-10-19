# Go2 전체 토픽

[운용 안내](../README.md#토픽-인터페이스)

원본 토픽은 아래 이름 그대로 사용한다. 지도·음성·확장 장치 토픽은 해당 기능이 동작할 때 데이터를 제공한다.

## 상태·제어

| 토픽 | 메시지 타입 | 내용 |
|---|---|---|
| `/config_change_status` | `unitree_go/msg/ConfigChangeStatus` | 설정 변경 알림 |
| `/lf/battery_alarm` | `std_msgs/msg/String` | 배터리 알림 |
| `/lf/bmsstate` | `unitree_hg/msg/BmsState` | BMS 상태 |
| `/lf/lowstate` | `unitree_go/msg/LowState` | 저주기 관절·IMU·모터·BMS 상태 |
| `/lf/sportmodestate` | `unitree_go/msg/SportModeState` | 저주기 동작 상태 |
| `/lowcmd` | `unitree_go/msg/LowCmd` | 저수준 관절 명령 |
| `/lowstate` | `unitree_go/msg/LowState` | 관절·IMU·모터·BMS 상태 |
| `/lowstate` | `unitree_hg/msg/LowState` | 관절·IMU·모터·BMS 상태 |
| `/sportmodestate` | `unitree_go/msg/SportModeState` | 고주기 동작 상태 |
| `/uwbstate` | `unitree_go/msg/UwbState` | UWB 상태 |
| `/uwbswitch` | `unitree_go/msg/UwbSwitch` | UWB 설정 |
| `/wirelesscontroller` | `unitree_go/msg/WirelessController` | 조종기 입력 |
| `/wirelesscontroller_unprocessed` | `unitree_go/msg/WirelessController` | 조종기 원시 입력 |

## 내장 센서

| 토픽 | 메시지 타입 | 내용 |
|---|---|---|
| `/frontvideostream` | `unitree_go/msg/Go2FrontVideoData` | 전면 카메라 압축 스트림 |
| `/utlidar/client_command` | `std_msgs/msg/String` | LiDAR 클라이언트 명령 |
| `/utlidar/cloud` | `sensor_msgs/msg/PointCloud2` | 센서 좌표계 포인트클라우드 |
| `/utlidar/cloud_base` | `sensor_msgs/msg/PointCloud2` | 본체 좌표계 포인트클라우드 |
| `/utlidar/cloud_deskewed` | `sensor_msgs/msg/PointCloud2` | 움직임 보정 포인트클라우드 |
| `/utlidar/grid_map` | `sensor_msgs/msg/PointCloud2` | 격자 지도 |
| `/utlidar/height_map` | `sensor_msgs/msg/PointCloud2` | 높이 지도 포인트클라우드 |
| `/utlidar/height_map_array` | `unitree_go/msg/HeightMap` | 높이 지도 배열 |
| `/utlidar/imu` | `sensor_msgs/msg/Imu` | LiDAR IMU |
| `/utlidar/lidar_state` | `unitree_go/msg/LidarState` | LiDAR 상태 |
| `/utlidar/mapping_cmd` | `std_msgs/msg/String` | 매핑 명령 |
| `/utlidar/range_info` | `geometry_msgs/msg/PointStamped` | 거리 정보 |
| `/utlidar/range_map` | `sensor_msgs/msg/PointCloud2` | 거리 지도 |
| `/utlidar/robot_odom` | `nav_msgs/msg/Odometry` | LiDAR 오도메트리 |
| `/utlidar/robot_pose` | `geometry_msgs/msg/PoseStamped` | LiDAR 추정 자세 |
| `/utlidar/server_log` | `std_msgs/msg/String` | LiDAR 로그 |
| `/utlidar/switch` | `std_msgs/msg/String` | LiDAR 스위치 |
| `/utlidar/voxel_map` | `sensor_msgs/msg/PointCloud2` | 복셀 지도 |
| `/utlidar/voxel_map_compressed` | `unitree_go/msg/VoxelMapCompressed` | 압축 복셀 지도 |

## 지도·위치 추정

| 토픽 | 메시지 타입 | 내용 |
|---|---|---|
| `/lio_sam_ros2/mapping/odometry` | `nav_msgs/msg/Odometry` | 매핑 오도메트리 |
| `/pctoimage_local` | `unitree_interfaces/msg/PcToImage` | 지도 영상 변환 |
| `/qt_add_edge` | `unitree_interfaces/msg/QtEdge` | 경로 연결 추가 |
| `/qt_add_node` | `unitree_interfaces/msg/QtNode` | 경로 지점 추가 |
| `/qt_command` | `unitree_interfaces/msg/QtCommand` | 경로 명령 |
| `/qt_notice` | `std_msgs/msg/String` | 지도·경로 알림 |
| `/query_result_edge` | `unitree_interfaces/msg/QtEdge` | 경로 연결 조회 결과 |
| `/query_result_node` | `unitree_interfaces/msg/QtNode` | 경로 지점 조회 결과 |
| `/slam_info` | `std_msgs/msg/String` | SLAM 정보 |
| `/slam_key_info` | `std_msgs/msg/String` | SLAM 키 정보 |
| `/uslam/client_command` | `std_msgs/msg/String` | SLAM 명령 |
| `/uslam/cloud_map` | `sensor_msgs/msg/PointCloud2` | SLAM 지도 |
| `/uslam/frontend/cloud_world_ds` | `sensor_msgs/msg/PointCloud2` | SLAM 전처리 포인트클라우드 |
| `/uslam/frontend/odom` | `nav_msgs/msg/Odometry` | SLAM 전처리 오도메트리 |
| `/uslam/localization/cloud_world` | `sensor_msgs/msg/PointCloud2` | 위치 추정 포인트클라우드 |
| `/uslam/localization/odom` | `nav_msgs/msg/Odometry` | 위치 추정 오도메트리 |
| `/uslam/map_file_pub` | `sensor_msgs/msg/PointCloud2` | 지도 파일 출력 |
| `/uslam/map_file_sub` | `sensor_msgs/msg/PointCloud2` | 지도 파일 입력 |
| `/uslam/navigation/global_path` | `sensor_msgs/msg/PointCloud2` | 전역 경로 |
| `/uslam/server_log` | `std_msgs/msg/String` | SLAM 로그 |

## 음성·영상 통신

| 토픽 | 메시지 타입 | 내용 |
|---|---|---|
| `/audio_msg` | `std_msgs/msg/String` | 음성 메시지 |
| `/audiohub/player/state` | `std_msgs/msg/String` | 오디오 재생 상태 |
| `/audioreceiver` | `unitree_go/msg/AudioData` | 수신 오디오 |
| `/audiosender` | `unitree_go/msg/AudioData` | 송신 오디오 |
| `/videohub/inner` | `std_msgs/msg/String` | 영상 내부 메시지 |
| `/webrtcreq` | `std_msgs/msg/String` | WebRTC 요청 |
| `/webrtcres` | `std_msgs/msg/String` | WebRTC 응답 |
| `/xfk_webrtcreq` | `std_msgs/msg/String` | WebRTC 확장 요청 |
| `/xfk_webrtcres` | `std_msgs/msg/String` | WebRTC 확장 응답 |

## 확장·시스템

| 토픽 | 메시지 타입 | 내용 |
|---|---|---|
| `/arm/action/state` | `std_msgs/msg/String` | 로봇팔 동작 상태 |
| `/arm_Command` | `unitree_arm/msg/ArmString` | 로봇팔 명령 |
| `/arm_Feedback` | `unitree_arm/msg/ArmString` | 로봇팔 피드백 |
| `/arm_sdk` | `unitree_hg/msg/LowCmd` | 로봇팔 저수준 명령 |
| `/gas_sensor` | `std_msgs/msg/String` | 가스 센서 |
| `/gesture/result` | `std_msgs/msg/String` | 제스처 인식 결과 |
| `/gnss` | `std_msgs/msg/String` | GNSS 정보 |
| `/gpt_cmd` | `std_msgs/msg/String` | 음성·AI 명령 |
| `/gpt_msg` | `std_msgs/msg/String` | 음성·AI 메시지 |
| `/gpt_state` | `std_msgs/msg/String` | 음성·AI 상태 |
| `/gptflowfeedback` | `std_msgs/msg/String` | 음성·AI 실행 피드백 |
| `/multiplestate` | `std_msgs/msg/String` | 통합 상태 |
| `/pet/flowfeedback` | `std_msgs/msg/String` | 동작 실행 피드백 |
| `/programming_actuator/command` | `std_msgs/msg/String` | 프로그램 실행 명령 |
| `/programming_actuator/feedback` | `std_msgs/msg/String` | 프로그램 실행 피드백 |
| `/public_network_status` | `std_msgs/msg/String` | 외부 네트워크 상태 |
| `/rtc/state` | `std_msgs/msg/String` | RTC 상태 |
| `/rtc_status` | `std_msgs/msg/String` | RTC 연결 상태 |
| `/selftest` | `std_msgs/msg/String` | 자가 진단 |
| `/servicestate` | `std_msgs/msg/String` | 서비스 상태 |
| `/servicestateactivate` | `std_msgs/msg/String` | 서비스 활성화 |

## 서비스 API

요청은 `unitree_api/msg/Request`로 발행하고, 응답은 `unitree_api/msg/Response`로 구독한다.

| 서비스 | 요청 토픽 | 응답 토픽 |
|---|---|---|
| arm | `/api/arm/request` | — |
| assistant_recorder | `/api/assistant_recorder/request` | `/api/assistant_recorder/response` |
| audiohub | `/api/audiohub/request` | `/api/audiohub/response` |
| bashrunner | `/api/bashrunner/request` | `/api/bashrunner/response` |
| config | `/api/config/request` | `/api/config/response` |
| fourg_agent | `/api/fourg_agent/request` | `/api/fourg_agent/response` |
| gas_sensor | `/api/gas_sensor/request` | `/api/gas_sensor/response` |
| gesture | `/api/gesture/request` | — |
| gpt | `/api/gpt/request` | `/api/gpt/response` |
| motion_switcher | `/api/motion_switcher/request` | `/api/motion_switcher/response` |
| obstacles_avoid | `/api/obstacles_avoid/request` | `/api/obstacles_avoid/response` |
| pet | `/api/pet/request` | `/api/pet/response` |
| programming_actuator | `/api/programming_actuator/request` | `/api/programming_actuator/response` |
| rm_con | `/api/rm_con/request` | — |
| robot_state | `/api/robot_state/request` | `/api/robot_state/response` |
| slam_operate | `/api/slam_operate/request` | `/api/slam_operate/response` |
| sport | `/api/sport/request` | `/api/sport/response` |
| sport_lease | `/api/sport_lease/request` | `/api/sport_lease/response` |
| uwbswitch | `/api/uwbswitch/request` | `/api/uwbswitch/response` |
| videohub | `/api/videohub/request` | `/api/videohub/response` |
| vla | `/api/vla/request` | `/api/vla/response` |
| voice | `/api/voice/request` | `/api/voice/response` |
| vui | `/api/vui/request` | `/api/vui/response` |

API 번호·인자는 [Unitree SDK2](https://github.com/unitreerobotics/unitree_sdk2/tree/main/include/unitree/robot/go2)를 따른다.
