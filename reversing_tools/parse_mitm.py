#!/usr/bin/env python

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import json
from cStringIO import StringIO
from libmproxy.flow import FlowReader
from inform import InformSerializer


def make_serializer(from_file):
    with open(from_file) as fp:
        keystore = {i['mac']: i['x_authkey'] for i in json.load(fp)}

    return InformSerializer("", keystore)


def dumps_pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': '))


if __name__ == "__main__":
    ser = make_serializer("data/devices.json")

    with open('data/mitm/onoff.txt', 'rb') as fp, open('test.out', 'w') as fp2:
        read = FlowReader(fp)

        for rec in read.stream():
            res = ser.parse(StringIO(rec.response.content))
            req = ser.parse(StringIO(rec.request.content))

            # print req.payload
            if res.payload['_type'] == 'cmd':
                print dumps_pretty(res.payload)
            # print dumps_pretty(req.payload)
            # print dumps_pretty(res.payload)
            print
