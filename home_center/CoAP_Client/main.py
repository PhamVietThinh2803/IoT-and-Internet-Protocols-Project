import asyncio
import json
from time import sleep
import requests
from aiocoap import *

# HTTP Client POST request to server THINGSBOARD
url_post = 'http://e4fd-202-191-58-174.ngrok-free.app/api/v1/3i58kz8UHbZX0v8iWgnJ/telemetry'
headers = {'content-type': 'application/json'}


# Function to check whether a message is JSON
def is_JSON(message):
    try:
        json.loads(message)
    except ValueError as err:
        return False
    return True


async def main():
    global df
    protocol = await Context.create_client_context()

    request = Message(code=GET, uri='coap://192.168.0.112/Espressif')

    try:
        response = await protocol.request(request).response
    except Exception as e:
        print('Failed to fetch resource: ')
        print(e)
    else:
        message = json.loads(response.payload.decode('utf-8'))
        temperature = message["temperature"]
        humidity = message["humidity"]

        payload = json.dumps({"temperature_CoAP": temperature, "humidity_CoAP": humidity})
        r1 = requests.post(url=url_post, data=payload, headers=headers)
        while(r1.status_code != 200):
            r1 = requests.post(url=url_post, data=payload, headers=headers)
            print("Retrying to send data to Thingsboard")
        print("Successfully send data to Thingsboard")
        print("Sleep 5 seconds until send next command to CoAP Server")
        sleep(5)

if __name__ == "__main__":
    while True:
        asyncio.run(main())
