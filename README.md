| Supported Targets | ESP32 | ESP32-C3 | ESP32-S2 | ESP32-S3 |
| ----------------- | ----- | -------- | -------- | -------- |

# IoT-and-Internet-Protocols-Project
This demo shows how to implement communication between ESP32 and a central controller via two protocols MQTT and CoAP. The two ESP32 sensor nodes use the ESP-IDF platform. To be able to use it, download the ESP-IDF according to the manufacturer's instructions
https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/index.html
The central controller emulates an embedded computer that receives and processes information from 2 ESP32 nodes, and then pushes the information onto the thingsboard via HTTP protocol. Software for central controller implemented in python.


