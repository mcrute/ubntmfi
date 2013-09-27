import os
import json
from keystore import KEYSTORE
from cStringIO import StringIO
from inform import InformSerializer, Cryptor


PATH = "/Users/mcrute/Desktop/test2"


for file in os.listdir(PATH):
    ser = InformSerializer()

    with open(os.path.join(PATH, file)) as fp:
        packet = ser.parse(fp)

    ser.key = KEYSTORE[packet.formatted_mac_addr]

    ser._decrypt_payload(packet)


    payload = packet.payload

    print json.dumps(payload, sort_keys=True, indent=4)
