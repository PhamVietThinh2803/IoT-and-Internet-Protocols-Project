import requests
import json
from aiocoap import *
import asyncio
from time import sleep
count = 0

# HTTP Client GET request to get command from server
url_get = 'http://e4fd-202-191-58-174.ngrok-free.app/api/v1/3i58kz8UHbZX0v8iWgnJ/rpc?timeout=20000'
url_post = 'http://e4fd-202-191-58-174.ngrok-free.app/api/v1/3i58kz8UHbZX0v8iWgnJ/attributes'
headers = {'content-type': 'application/json'}
# CoAP Server URI
coap_uri = "coap://192.168.0.112/Espressif"


async def put_request():
    """Perform a single PUT request to desired URI"""

    context = await Context.create_client_context()

    await asyncio.sleep(2)
    payload = b'On'

    request = Message(code=PUT, payload=payload, uri=coap_uri)
    response = await context.request(request).response
    print('Result: %s' % (response.code))
    print('Successfully sent request to CoAP node')
    button_payload = "{'CoAP_Button': 'False'}"
    print('Turn off server button dashboard')
    r1 = requests.post(url=url_post, data=button_payload, headers=headers)
    if r1.status_code == 200:
        print('Successfully turn off server button dashboard')

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
            if method == 'To CoAP Node':
                try:
                    asyncio.run(put_request())
                except Exception as e:
                    print('Error: ', e)
                    print('Check the CoAP Server connection')
            else:
                print('Thingsboard server is temporary closed. Turn off all the peripherals!')
                asyncio.run(put_request())
                print('Waiting ...')
                sleep(500)


    