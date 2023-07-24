import paho.mqtt.client as mqtt
import requests
import json
from time import sleep

# HTTP Client GET request to get command from server
url_get = 'http://e4fd-202-191-58-174.ngrok-free.app/api/v1/3i58kz8UHbZX0v8iWgnJ/rpc?timeout=20000'
# MQTT Broker Parameters
broker_uri = "test.mosquitto.org"
port = 8883


def on_publish(client, userdata, result):
    print("Successfully sending request to MQTT node\n")


while True:
    try:
        r = requests.get(url=url_get)
    except Exception as e:
        print('Error: ', e)
    else:
        print('Status code: ' + str(r.status_code))
        if r.status_code == 200:
            print(r.json())
            message = json.loads(r.text)
            method = message["method"]
            params = message["params"]
            if method == 'To MQTT Node':
                client = mqtt.Client()
                client.tls_set(ca_certs='mqtt_cert/mosquitto.org.crt', certfile='mqtt_cert/client.crt',
                           keyfile='mqtt_cert/client.key')
                client.on_publish = on_publish
                client.connect(broker_uri, port, keepalive=60)
                client.loop_start()
                if params:
                    client.publish("ESP32/command", "On")
                else:
                    client.publish("ESP32/command", "Off")
                client.loop_stop()
        else:
            print('Thingsboard server is off!')
            print('Turn off MQTT Node LED for safety')
            client = mqtt.Client()
            client.tls_set(ca_certs='mqtt_cert/mosquitto.org.crt', certfile='mqtt_cert/client.crt',
                           keyfile='mqtt_cert/client.key')
            client.on_publish = on_publish
            client.connect(broker_uri, port, keepalive=60)
            client.loop_start()
            client.publish("ESP32/command", "default")
            client.loop_stop()
            print('Go to sleep waiting for Thingsboard server ...')
            sleep(500)
        