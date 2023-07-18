import requests
import json
from aiocoap import *
import asyncio

# HTTP Client GET request to get command from server
url_get = 'http://e4fd-202-191-58-174.ngrok-free.app/api/v1/3i58kz8UHbZX0v8iWgnJ/rpc?timeout=20000'
# CoAP Server URI
coap_uri = "coap://192.168.0.112/Espressif"


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
            if method == 'To CoAP Node':
                try:
                    asyncio.run(put_request(True))
                except Exception as e:
                    print('Error: ', e)
                    print('Check the CoAP Server connection')
                else:
                    print('Successfully sent request to server')
    