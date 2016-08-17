#!/usr/bin/env python

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import dpkt
import json
from cStringIO import StringIO
from inform import InformSerializer


def go_debug(filename):
    arr = lambda x: [ord(i) for i in x]
    packet = ser.parse(open('test_files/2.bin'))
    return {
        "magic": packet.magic_number,
        "version": packet.version,
        "mac": arr(packet.mac_addr),
        "flags": packet.flags,
        "iv": arr(packet.iv),
        "data_version": packet.data_version,
        "data_len": packet.data_length,
        "raw_payload": json.packet.raw_payload,
        "formatted_mac": packet.formatted_mac_addr,
        "is_enc": packet.is_encrypted,
        "is_comp": packet.is_compressed,
    }


def collect_records(from_file):
    records = []
    buffer = StringIO()

    for ts, buf in dpkt.pcap.Reader(open(from_file)):
        eth = dpkt.ethernet.Ethernet(buf)
        data = eth.data.tcp.data.split("\r\n")[-1]

        if data.startswith("TNBU") and buffer.tell() != 0:
            records.append(buffer.getvalue())
            buffer.seek(0)
            buffer.write(data)
        else:
            buffer.write(data)

    return records


def make_serializer(from_file):
    with open(from_file) as fp:
        keystore = { i['mac']: i['x_authkey'] for i in json.load(fp) }

    return InformSerializer("", keystore)


if __name__ == "__main__":
    ser = make_serializer("devices.json")

    for i, data in enumerate(collect_records("mfi.out")):
        try:
            packet = ser.parse(StringIO(data))
            print packet.raw_payload
        except ValueError:
            pass
