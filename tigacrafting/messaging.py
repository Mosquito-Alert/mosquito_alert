import ssl
import json
import socket
import struct
import binascii

def send_message_ios(token,alert_message,link_url):
    cert = '/home/webuser/webapps/tigaserver/CertificatMosquito.pem'
    TOKEN = token
    PAYLOAD = {
        'aps': {
            'alert': alert_message,
            'sound': 'default',
            'link_url': link_url
        }
    }

    # APNS development server
    apns_address = ('gateway.sandbox.push.apple.com', 2195)

    # Use a socket to connect to APNS over SSL
    s = socket.socket()
    sock = ssl.wrap_socket(s, certfile=cert)
    sock.connect(apns_address)

    # Generate a notification packet
    TOKEN = binascii.unhexlify(TOKEN)
    PAYLOAD = json.dumps(PAYLOAD)
    fmt = '!cH32sH{0:d}s'.format(len(PAYLOAD))
    cmd = '\x00'
    message = struct.pack(fmt, cmd, len(TOKEN), TOKEN, len(PAYLOAD), PAYLOAD)

    response = sock.write(message)
    print response
    sock.close()
