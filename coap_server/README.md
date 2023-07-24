| Supported Targets | ESP32 | ESP32-C3 | ESP32-S2 | ESP32-S3 |
| ----------------- | ----- | -------- | -------- | -------- |

# CoAP server example

This CoAP server example is very simplified adaptation of one of the
[libcoap](https://github.com/obgm/libcoap) examples.

CoAP server example will startup a daemon task, receive requests / data from CoAP client and transmit
data to CoAP client.

If the incoming request requests the use of DTLS (connecting to port 5684), then the CoAP server will
try to establish a DTLS session using the previously defined Pre-Shared Key (PSK) - which
must be the same as the one that the CoAP client is using, or Public Key Infrastructure (PKI) where
the PKI information must match as requested.

The Constrained Application Protocol (CoAP) is a specialized web transfer protocol for use with
constrained nodes and constrained networks in the Internet of Things.
The protocol is designed for machine-to-machine (M2M) applications such as smart energy and
building automation.

Please refer to [RFC7252](https://www.rfc-editor.org/rfc/pdfrfc/rfc7252.txt.pdf) for more details.

## How to use example

### Configure the project

```
idf.py menuconfig
```

Example Connection Configuration  --->
 * Set WiFi SSID
 * Set WiFi Password
Component config  --->
  CoAP Configuration  --->
    * Set encryption method definition, PSK (default) or PKI
    * Enable CoAP debugging if required
    * Disable CoAP using TCP if this is not required (TCP needed for TLS)
    * Disable CoAP client functionality to reduce code size unless this server is a proxy
Example CoAP Server Configuration  --->
 * If PSK, Set CoAP Preshared Key to use for connections to the server

### Build and Flash

Build the project and flash it to the board, then run monitor tool to view serial output:

```
idf.py build
idf.py -p PORT flash monitor
```

(To exit the serial monitor, type ``Ctrl-]``.)

See the Getting Started Guide for full steps to configure and use ESP-IDF to build projects.

## Example Output

If a CoAP client queries the `/Espressif` resource, CoAP server will return temperature and humidity data 
if it is a GET request. To PUT request, CoAP server will process the payload to decide to turn On/Off LED.

## libcoap Documentation
This can be found at [libcoap Documentation](https://libcoap.net/documentation.html).
The current API is 4.3.0.

## libcoap Specific Issues
These can be raised at [libcoap Issues](https://github.com/obgm/libcoap/issues).

## Troubleshooting
* Please make sure CoAP client fetchs or puts data under path: `/Espressif` or
fetches `/.well-known/core`

* CoAP logging can be enabled by running 'idf.py menuconfig -> Component config -> CoAP Configuration -> Enable CoAP debugging'
and setting appropriate log level.  If Mbed TLS logging is required, this needs to be configured separately under mbedTLS
Component Configuration and the CoAP logging level set to mbedTLS.
