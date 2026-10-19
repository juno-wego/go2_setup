cmake_minimum_required(VERSION 3.16)
project(mid360 LANGUAGES NONE)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)

# The SDK is built first by scripts/build_sdk.sh into this package's prefix.
# Keeping it separate avoids a build dependency cycle with livox_ros_driver2.
ament_python_install_package(${PROJECT_NAME})
ament_environment_hooks("${CMAKE_CURRENT_SOURCE_DIR}/env/mid360.dsv")
install(DIRECTORY launch config DESTINATION share/${PROJECT_NAME})
install(FILES README.md DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(configuration test/test_mid360_configuration.py)
endif()

ament_package()
