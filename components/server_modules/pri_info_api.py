#! /home/sud/.virtualenvs/aawaz/bin/python
import tornado.ioloop
import tornado.web
import redis
import pymongo
from bson.json_util import dumps


consumer_port = 9999


class MainHandler(tornado.web.RequestHandler):
    def get(self, server):
        mongo_client = pymongo.MongoClient(host="localhost")
        if server == "all":
            cursor = mongo_client["pritesterdb"]["pri_status_collection"].find({})
            data = dumps(cursor)
            print data
            self.write(data)
        else:
            cursor = mongo_client["pritesterdb"]["pri_status_collection"].find({"ipaddr_private": server})
            data = dumps(cursor)
            print data
            self.write(data)





application = tornado.web.Application(
    handlers=[
        (r"/pri_info/(?P<server>.*?)", MainHandler),
    ])

if __name__ == "__main__":
    application.listen(consumer_port)
    print "pri info consumer started at port {}".format(consumer_port)
    tornado.ioloop.IOLoop.instance().start()
