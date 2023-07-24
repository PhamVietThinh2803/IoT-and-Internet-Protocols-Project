import paho.mqtt.client as mqtt
import json
from time import sleep
import requests

# HTTP Client POST request to server THINGSBOARD
url_post = 'http://e4fd-202-191-58-174.ngrok-free.app/api/v1/3i58kz8UHbZX0v8iWgnJ/telemetry'
headers = {'content-type': 'application/json'}
# MQTT Broker Parameters
broker_uri = "test.mosquitto.org"
port = 8883
# Variable represents whether still connected to Thingsboard
flag = 0 
retry = 0

# Function to check whether a message is JSON
def is_JSON(message):
    try:
        json.loads(message)
    except ValueError as err:
        return False
    return True


# The callback for when the client receives a CONNACK response from the server.
# mean that if we lose the connection and reconnect then subscriptions will be renewed.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    print("Connected to Mosquitto Broker!")
    client.subscribe("ESP32/data")


# Callback function for when a published message is received from the server.
def on_message(client, userdata, msg):
    global flag
    global retry
    print("Data from topic: " + msg.topic)
    if is_JSON(msg.payload.decode('utf-8')):
        message = json.loads(msg.payload.decode('utf-8'))
        print(message)
        temperature = message["temperature"]
        humidity = message["humidity"]

        payload = json.dumps({"temperature_mqtt": temperature, "humidity_mqtt": humidity})
        try:
            r1 = requests.post(url=url_post, data=payload, headers=headers)
        except Exception as e:
            print('Error:', e)
        else:
            if r1.status_code == 200:
                print("Successfully send data to Thingsboard")
            else:
                print('Thingsboard server is off!')
                print('Waiting ....')
                sleep(500)

    else:
        print(msg.payload.decode('utf-8'))
    print("Sleep 5 seconds until send next command to MQTT Node")
    sleep(5)
    print("Requesting MQTT Node to send data")
    client.publish("ESP32/command", "data")


def on_publish(client, userdata, result):
    print("Successfully sending request to MQTT node to send data\n")


def on_subscribe(client, userdata, mid, granted_qos):
    print("Successfully connected to ESP32/data topic")
    print("Sending first request to the MQTT node")
    client.publish("ESP32/command", "data")


def on_disconnect(client, userdata, msg):
    print("Disconnecting from Server. Trying to reconnect!")


# Client Initialize
client = mqtt.Client()
client.tls_set(ca_certs='mqtt_cert/mosquitto.org.crt', certfile='mqtt_cert/client.crt', keyfile='mqtt_cert/client.key')
client.connect(broker_uri, port, keepalive=60)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.on_subscribe = on_subscribe
client.on_publish = on_publish
client.loop_forever()
