import os
import subprocess
import tornado.web
import tornado.ioloop
import tornado.options
import tornado.process
import tornado.template
import tornado.httpserver
from mfiapi import MFiAPI
from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)


class PowerStatusHandler(tornado.web.RequestHandler):

    def __init__(self, *args, **kwargs):
        self.api = MFiAPI('172.16.0.38:6443')
        super(PowerStatusHandler, self).__init__(*args, **kwargs)

    def get(self):
        self.api.login('admin', 'password')
        self.finish(self.api.port_status())

    def post(self):
        self.api.login('admin', 'password')

        for key, value in self.request.arguments.items():
            self.api.toggle_port(key)


class IndexHandler(tornado.web.RequestHandler):

    def __init__(self, *args, **kwargs):
        self.api = MFiAPI('172.16.0.38:6443')
        super(IndexHandler, self).__init__(*args, **kwargs)

    def get(self):
        self.api.login('admin', 'password')

        ports = [(port, port.replace(" ", "_").replace("'", "-")) for port in self.api.port_status().keys()]

        self.render("index.html", ports=ports)


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r"/power-status/?", PowerStatusHandler),
            (r"/?", IndexHandler),
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=True,
            autoescape=None,
        )
        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
