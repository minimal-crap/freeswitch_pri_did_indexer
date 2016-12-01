#! /home/sud/.virtualenvs/aawaz/bin/python
import tornado.ioloop
import tornado.web
import redis
import requests
import time


consumer_port = 1611
pri_info_consumer_api = "http://localhost:8888/publish_did_number/11111111"

class MainHandler(tornado.web.RequestHandler):
    def get(self, did_number):
        resp = requests.get(pri_info_consumer_api)
        time.sleep(1)
        self.write_error(resp.status_code)


application = tornado.web.Application(
    handlers=[
        (r"/originate_call/([0-9]+)", MainHandler)
    ]
)

if __name__ == "__main__":
    application.listen(consumer_port)
    print "freeswitch api simulator started on port : {}".format(consumer_port)
    tornado.ioloop.IOLoop.instance().start()
