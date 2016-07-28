import dpkt
import json
import binascii
from cStringIO import StringIO
from inform import InformSerializer, Cryptor


d = json.load(open("devices.json"))
KEYSTORE = { i['mac']: i['x_authkey'] for i in d }


def add_colons_to_mac(mac_addr):
    mac_addr = binascii.hexlify(mac_addr)
    return ":".join([mac_addr[i*2:i*2+2] for i in range(12/2)]).lower()


records = []
buffer = StringIO()

for ts, buf in dpkt.pcap.Reader(open("mfi.out")):
    eth = dpkt.ethernet.Ethernet(buf)
    data = eth.data.tcp.data.split("\r\n")[-1]

    if data.startswith("TNBU") and buffer.tell() != 0:
        records.append(buffer.getvalue())
        buffer.seek(0)
        buffer.write(data)
    else:
        buffer.write(data)


ser = InformSerializer("", KEYSTORE)
for data in records:
    try:
        packet = ser.parse(StringIO(data))
        print packet.raw_payload
    except:
        print "BAD"
        continue
