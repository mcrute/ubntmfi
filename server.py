import os
import subprocess
import tornado.web
import tornado.ioloop
import tornado.options
import tornado.process
import tornado.template
import tornado.httpserver
from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)


STATUSES = {
    'relay1': True,  # Fan
    'relay2': False, # Light
    'relay3': False,
}


# for relay in STATUSES.keys():
#     caller = subprocess.Popen(["ssh","admin@10.0.1.15",
#         "cat /proc/power/{}".format(relay)], stdout=subprocess.PIPE)
#     output = caller.communicate()[0]
#     STATUSES[relay] = output.startswith("1")


class PowerStatusHandler(tornado.web.RequestHandler):

    def get(self):
        self.finish(STATUSES)

    @tornado.web.asynchronous
    def _trigger_relay(self, relay, value):
        STATUSES[relay] = value
        value = 1 if value is True else 0
        tornado.process.Subprocess(["ssh","admin@10.0.1.15",
            "echo {} > /proc/power/{}".format(value, relay)],
                stdout=tornado.process.Subprocess.STREAM)

    def post(self):
        for key, value in self.request.arguments.items():
            self._trigger_relay(key, value[0] == "on")

        self.finish(STATUSES)


class IndexHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("index.html")


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
