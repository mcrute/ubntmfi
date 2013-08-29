import json
import urllib2
import urllib
from cookielib import CookieJar

def bool_to_bin(value):
    return 1 if value == True else 0


def bin_to_bool(value):
    return True if int(value) == 1 else False


class MFiAPI(object):

    def __init__(self, host):
        self.host = host
        self.opener = urllib2.build_opener(
                urllib2.HTTPCookieProcessor(CookieJar()))

    def _make_url(self, suffix):
        return 'https://{}/{}'.format(self.host, suffix)

    def login(self, username, password):
        form_data = urllib.urlencode({
            'username' : username,
            'password': password,
            'login': 'login'
        })

        self.opener.open(self._make_url('login'), form_data)

    def get_sensor_data(self):
        resp = self.opener.open(self._make_url('api/v1.0/list/sensors'))
        return json.load(resp)['data']

    def port_status(self):
        data = self.get_sensor_data()
        return dict((i['label'], bin_to_bool(i['output_val'])) for i in data)

    def set_port(self, mac, port, value):
        data = urllib.urlencode({ "json": json.dumps({
            "mac": mac,
            "val": bool_to_bin(value),
            "port": int(port),
            "cmd": "mfi-output"
            })
        })

        self.opener.open(self._make_url("api/v1.0/cmd/devmgr"), data)

    def toggle_port(self, name):
        mac, port, status = None, None, None

        for data in self.get_sensor_data():
            if data['label'] == name:
                set_to = not bin_to_bool(data['output_val'])
                self.set_port(data['mac'], data['port'], set_to)
