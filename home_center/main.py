import paho.mqtt.client as mqtt
import requests
import json

# HTTP Client GET request to get command from server
url_get = 'https://demo.thingsboard.io/api/v1/cdnUhlgFN2AlfXoiuWAj/rpc?timeout=20000'
# MQTT Broker Parameters
broker_uri = "test.mosquitto.org"
port = 8883

# The callback for when the client receives a CONNACK response from the server.
# mean that if we lose the connection and reconnect then subscriptions will be renewed.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    print("Connected to Mosquitto Broker!")
    client.subscribe("ESP32/data")

def on_publish(client, userdata, result):
    print("Successfully sending request to MQTT node to send data\n")

while True:
    r = requests.get(url=url_get)
    print('Status code: ' + str(r.status_code))
    if r.status_code == 200:
        print(r.json())
        message = json.loads(r.text)
        method = message["method"]
        params = message["params"]
        print(method)
        print(params)
        if method == 'Node 1 Controller':
            client = mqtt.Client()
            client.tls_set(ca_certs='Cert/mosquitto.org.crt', certfile='Cert/client.crt', keyfile='Cert/client.key')
            client.on_connect = on_connect
            client.on_publish = on_publish
            client.connect(broker_uri, port, keepalive=60)
            client.loop_start()
            client.publish("ESP32/command", "reboot")
            client.loop_stop()

    else:
        continue
