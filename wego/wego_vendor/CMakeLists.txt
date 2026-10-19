cmake_minimum_required(VERSION 3.8)
project(wego_vendor LANGUAGES NONE)

find_package(ament_cmake REQUIRED)

ament_environment_hooks(
  env-hooks/vendor_paths.dsv.in
  env-hooks/wego_defaults.sh.in
)

install(FILES README.md DESTINATION share/${PROJECT_NAME})
ament_package()
