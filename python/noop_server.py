#!/usr/bin/python

from StringIO import StringIO
from SocketServer import TCPServer
from inform import InformSerializer
from ConfigParser import SafeConfigParser
from SimpleHTTPServer import  SimpleHTTPRequestHandler


class Handler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        SimpleHTTPRequestHandler.__init__(self, *args, **kwargs)
        self.parser = InformSerializer(key_bag=get_keys("inform.cfg"))

    def _get_keys(self, filename):
        cfg = SafeConfigParser()
        cfg.read(filename)

        return dict((sect, cfg.get(sect, "authkey"))
                for sect in cfg.sections())

    def do_POST(self):
        length = int(self.headers['content-length'])
        body = StringIO(self.rfile.read(length))
        packet = self.parser.parse(body)

        noop_packet = packet.response_copy()
        noop_packet.payload = { "_type": "noop", "interval": 10 }

        buffer = StringIO(self.parser.serialize(noop_packet))

        self.send_response(200)
        self.send_header("Content-type", "application/x-binary")
        self.send_header("Connection", "close")
        self.send_header("User-Agent", "Unifi Controller")
        self.send_header("Content-Length", buffer.len)
        self.end_headers()

        return buffer


httpd = TCPServer(("", 9966), Handler)
print "serving on 9966"
httpd.serve_forever()
