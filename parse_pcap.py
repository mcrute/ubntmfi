import dpkt
import binascii
from keystore import KEYSTORE
from cStringIO import StringIO
from inform import InformSerializer, Cryptor


def add_colons_to_mac(mac_addr):
    mac_addr = binascii.hexlify(mac_addr)
    return ":".join([mac_addr[i*2:i*2+2] for i in range(12/2)]).lower()


for ts, buf in dpkt.pcap.Reader(open("/Users/mcrute/Desktop/http_fast.pcap")):
    eth = dpkt.ethernet.Ethernet(buf)
    data = eth.data.tcp.data.split("\r\n")
    header, data = data[0], data[-1]

    keys = [
        KEYSTORE.get(add_colons_to_mac(eth.src)),
        KEYSTORE.get(add_colons_to_mac(eth.dst)),
        KEYSTORE.get("00:00:00:00:00:00")
    ]

    if not data.startswith("TNBU"):
        continue

    for key in keys:
        if key is None:
            continue

        ser = InformSerializer(key)

        try:
            packet = ser.parse(StringIO(data))
            ser._decrypt_payload(packet)

            if not packet.raw_payload.startswith("{"):
                continue
            else:
                break
        except ValueError as err:
            if '16' in err.message:
                #to_add = 16 - (len(data[40:]) % 16)
                #decrypted = Cryptor(KEY, packet.iv).decrypt(data[40:] + ("\x00" * to_add))
                continue
            else:
                raise

        packet = None


        if not packet:
            print "Bad Packet"
            continue
        else:
            print packet.raw_payload

        #type = packet.payload.get('_type', None)

        #if type and (not type == 'noop'):
        #    print packet.raw_payload
