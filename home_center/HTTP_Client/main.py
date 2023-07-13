import paho.mqtt.client as mqtt
import requests
import json
from aiocoap import *
import asyncio

# HTTP Client GET request to get command from server
url_get = 'http://e4fd-202-191-58-174.ngrok-free.app/api/v1/3i58kz8UHbZX0v8iWgnJ/rpc?timeout=20000'
coap_uri = "coap://192.168.0.104/Espressif"
# MQTT Broker Parameters
broker_uri = "test.mosquitto.org"
port = 8883


async def put_request(reff):
    """Perform a single PUT request to desired URI"""

    context = await Context.create_client_context()

    await asyncio.sleep(2)
    if reff == True:
        payload = b'On'
    else:
        payload = b'Off'

    request = Message(code=PUT, payload=payload, uri=coap_uri)
    response = await context.request(request).response
    print('Result: %s\n%r' % (response.code, response.payload.decode("utf-8")))


def on_publish(client, userdata, result):
    print("Successfully sending request to MQTT node\n")


while True:
    r = requests.get(url=url_get)
    print('Status code: ' + str(r.status_code))
    if r.status_code == 200:
        print(r.json())
        message = json.loads(r.text)
        method = message["method"]
        params = message["params"]
        if method == 'To CoAP Node':
            if params:
                asyncio.run(put_request(True))
            else:
                asyncio.run(put_request(False))
        else:
            client = mqtt.Client()
            client.tls_set(ca_certs='Cert/mosquitto.org.crt', certfile='Cert/client.crt',
                           keyfile='Cert/client.key')
            client.on_publish = on_publish
            client.connect(broker_uri, port, keepalive=60)
            client.loop_start()
            if params:
                client.publish("ESP32/command", "On")
            else:
                client.publish("ESP32/command", "Off")
            client.loop_stop()