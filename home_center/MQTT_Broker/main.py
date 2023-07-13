import paho.mqtt.client as mqtt
import json
import pandas as pd
from time import sleep
from datetime import datetime
import xlsxwriter
import requests

# HTTP Client POST request to server THINGSBOARD
url_post = 'https://demo.thingsboard.io/api/v1/cdnUhlgFN2AlfXoiuWAj/telemetry'
headers = {'content-type': 'application/json'}
# MQTT Broker Parameters
broker_uri = "test.mosquitto.org"
port = 8883
df = pd.DataFrame()
# Create a new xlsx file with name of timestamp
timestamp = datetime.now().strftime("%d.%m.%Y %H.%M.%S")
new_workbook = "Logging/{Time}.xlsx".format(Time=timestamp)
print(new_workbook)
workbook = xlsxwriter.Workbook(new_workbook)
workbook.close()


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
    global df
    print("Data from topic: " + msg.topic)
    if is_JSON(msg.payload.decode('utf-8')):
        message = json.loads(msg.payload.decode('utf-8'))
        info = message["info"]
        location = info["location"]
        floor = info["floor"]
        room = info["room"]
        data = message["data"]
        temperature = data["temperature"]
        humidity = data["humidity"]

        frame = {
            "Location": [location],
            "Floor": [floor],
            "Room": [room],
            "Temperature": [temperature],
            "Humidity": [humidity],
        }
        payload = json.dumps({"temperature": temperature, "humidity": humidity})
        # load data into a DataFrame object:
        df_temp = pd.DataFrame(frame)
        df = pd.concat([df, df_temp], ignore_index=True)
        print(df)
        df.to_excel(new_workbook)
        print(payload)
        r1 = requests.post(url=url_post, data=payload, headers=headers)
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
client.tls_set(ca_certs='Cert/mosquitto.org.crt', certfile='Cert/client.crt', keyfile='Cert/client.key')
client.connect(broker_uri, port, keepalive=60)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.on_subscribe = on_subscribe
client.on_publish = on_publish
client.loop_forever()
