#!/usr/bin/env python

import os
import json
import time
import paramiko
import contextlib
import subprocess

from keystore import USERNAME, PASSWORD, HOSTS


RRA_COMMON = [
    "RRA:AVERAGE:0.5:1:800",
    "RRA:AVERAGE:0.5:6:800",
    "RRA:AVERAGE:0.5:24:800",
    "RRA:AVERAGE:0.5:288:800",
    "RRA:MAX:0.5:1:800",
    "RRA:MAX:0.5:6:800",
    "RRA:MAX:0.5:24:800",
    "RRA:MAX:0.5:288:800",
]

RRD_TEMPLATES = {
    "interface": [
        "DS:packets_rx:COUNTER:600:0:U",
        "DS:packets_tx:COUNTER:600:0:U",
        "DS:bytes_rx:COUNTER:600:0:U",
        "DS:bytes_tx:COUNTER:600:0:U",
        "DS:errors_rx:COUNTER:600:0:U",
        "DS:errors_tx:COUNTER:600:0:U",
        "DS:dropped_rx:COUNTER:600:0:U",
        "DS:dropped_tx:COUNTER:600:0:U",
    ],
    "network": [
        "DS:packets_rx:COUNTER:600:0:U",
        "DS:packets_tx:COUNTER:600:0:U",
        "DS:bytes_rx:COUNTER:600:0:U",
        "DS:bytes_tx:COUNTER:600:0:U",
        "DS:retries_tx:COUNTER:600:0:U",
        "DS:stations:GAUGE:600:0:U",
    ],
    "station": [
        "DS:rssi:GAUGE:600:0:U",
        "DS:noise:GAUGE:600:U:U",
        "DS:signal:GAUGE:600:U:U",
        "DS:power:GAUGE:600:0:U",
        "DS:rate_rx:GAUGE:600:0:U",
        "DS:rate_tx:GAUGE:600:0:U",
        "DS:packets_rx:COUNTER:600:0:U",
        "DS:packets_tx:COUNTER:600:0:U",
        "DS:bytes_rx:COUNTER:600:0:U",
        "DS:bytes_tx:COUNTER:600:0:U",
    ],
}


@contextlib.contextmanager
def get_mca_data(host):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())
    client.connect(host, username=USERNAME, password=PASSWORD)
    _, stdout, _ = client.exec_command("mca-dump")

    yield json.loads(stdout.read())

    client.close()


@contextlib.contextmanager
def host_folder(host):
    if not os.path.exists(host):
        os.mkdir(host)

    os.chdir(host)
    yield
    os.chdir(os.path.dirname(os.getcwd()))


def rrd_update(kind, name, source, *stats):
    stats = ":".join(["N"] + list(str(int(source[key])) for key in stats))
    rrd_name = "{}-{}.rrd".format(kind, name)

    if not os.path.exists(rrd_name):
        command = ["rrdtool", "create", rrd_name]
        command.extend(RRD_TEMPLATES[kind])
        command.extend(RRA_COMMON)
        subprocess.call(command)

    subprocess.call(("rrdtool", "update", rrd_name, stats))


def update_eth(data):
    rrd_update("interface", "eth0", data, "rx_packets", "tx_packets",
            "rx_bytes", "tx_bytes", "rx_errors", "tx_errors", "rx_errors",
            "tx_errors")

def update_network(data):
    rrd_update("network", "{}_{}".format(data["essid"], data["radio"]), data,
            "rx_packets", "tx_packets", "rx_bytes", "tx_bytes", "tx_retries",
            "num_sta")


def update_station(data):
    rrd_update("station", data["mac"], data, "rssi", "noise", "signal",
            "tx_power", "rx_rate", "tx_rate", "rx_packets", "tx_packets",
            "rx_bytes", "tx_bytes")


while True:
    for host in HOSTS:
        print "Updating {}".format(host)
        with host_folder(host), get_mca_data(host) as data:
            update_eth(data["if_table"][0])

            for vap in data["vap_table"]:
                update_network(vap)

                for station in vap["sta_table"]:
                    update_station(station)

    print "=" * 80
    time.sleep(300)
