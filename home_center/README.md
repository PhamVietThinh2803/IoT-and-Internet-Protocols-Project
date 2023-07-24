# Home-Center

Structure of software for home center:
 * mqtt_broker.py: python file for MQTT Client. To get data from MQTT Node, it will send command "data" to topic "ESP32/data" every 5 seconds,
 process it then push to Thingsboard using HTTP POST. Connection using SSL with user-defined certification.
 * coap_client.py: python file for CoAP Client. To get data from CoAP Server, it will send GET request to desired Server IP and resource every 5 seconds,
 process it then push to Thingsboard using HTTP POST. 
 * coap_command.py: python file for home center to received command from ThingsBoard by RPC request, process the data then send command to CoAP Server by
 PUT requests.
 * mqtt_command.py: python file for home center to received command from ThingsBoard by RPC request, process the data then send command to MQTT Node by
 publish command to "ESP32/command" topic with payload "On"/"Off".
 * mqtt_cert: Certification for SSL MQTT