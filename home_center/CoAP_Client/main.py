import asyncio
import json
import requests
from aiocoap import *

# HTTP Client POST request to server THINGSBOARD
url_post = 'https://demo.thingsboard.io/api/v1/LRkilX7Ot2ZOLWplnpLn/telemetry'
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

    request = Message(code=GET, uri='coap://192.168.0.104/Espressif')

    try:
        response = await protocol.request(request).response
    except Exception as e:
        print('Failed to fetch resource: ')
        print(e)
    else:
        message = json.loads(response.payload.decode('utf-8'))
        temperature = message["temperature"]
        humidity = message["humidity"]

        payload = json.dumps({"temperature": temperature, "humidity": humidity})
        r1 = requests.post(url=url_post, data=payload, headers=headers)


if __name__ == "__main__":
    while True:
        asyncio.run(main())
