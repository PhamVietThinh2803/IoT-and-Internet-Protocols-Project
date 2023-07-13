# The following four lines of boilerplate have to be in your project's CMakeLists
# in this exact order for cmake to work correctly
cmake_minimum_required(VERSION 3.16)

# This example uses an extra component for some common functions such as Wi-Fi and Ethernet connection.
set(EXTRA_COMPONENT_DIRS $ENV{IDF_PATH}/examples/common_components/protocol_examples_common)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(mqtt_tcp)

target_add_binary_data(${CMAKE_PROJECT_NAME}.elf "Certs/client.crt" TEXT)
target_add_binary_data(${CMAKE_PROJECT_NAME}.elf "Certs/client.key" TEXT)
target_add_binary_data(${CMAKE_PROJECT_NAME}.elf "Certs/mosquitto.org.crt" TEXT)