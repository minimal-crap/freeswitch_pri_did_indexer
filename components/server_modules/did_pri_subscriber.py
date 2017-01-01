#! /home/sud/.virtualenvs/aawaz/bin/python
import redis
import threading
import json
from pymongo import MongoClient

mongo_client = MongoClient()
mongo_db = "pritesterdb"
mongo_db_collection = "pri_status_collection"


class Listener(threading.Thread):
    def __init__(self, r, channels):
        threading.Thread.__init__(self)
        self.redis = r
        self.mongo_client = MongoClient('localhost', 27017)
        self.pri_data = None
        self.pri_did = None
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(channels)

    def work(self, item):
        print item['channel'], ":", item['data']

    def run(self):
        for item in self.pubsub.listen():
            if item['data'] == "KILL":
                self.pubsub.unsubscribe()
                print self, "unsubscribed and finished"
                break
            else:
                self.work(item)
                try:
                    data = json.loads(item["data"])
                    if type(data) == dict:
                        self.pri_data = data
                    elif type(data) == int:
                        self.pri_did = data

                    if self.pri_data is not None and self.pri_did is not None:
                        # self.pri_data["did"] = self.pri_did
                        # print json.dumps(self.pri_data)
                        # self.mongo_client["pritesterdb"]["pri_status_collection"].insert_one(self.pri_data)
                        # print self.pri_data
                        # print self.pri_did
                        current_wanpipe = self.pri_data.keys()[0]
                        self.pri_data[current_wanpipe]["outgoing_caller_id"] = self.pri_did
                        # cursor = mongo_client["pritesterdb"]["pri_status_collection"].update(
                        #     {"wanpipe." + current_wanpipe: {"$exists": "true"},
                        #      "ipaddr_private": current_server}, {"$set": self.pri_data}, upsert=True
                        # )
                        count = self.redis.sadd("wan_pipes", self.pri_data)
                        print "added {} elements in wan_pipes redis key".format(count)


                        self.pri_data = None
                        self.pri_did = None

                except ValueError as err:
                    print "value error occurred::" + err.message
                except TypeError as err:
                    print "type error occurred::" + err.message
                except Exception as err:
                    print err.message

if __name__ == "__main__":
    r = redis.StrictRedis()
    client = Listener(r, ['outgoing'])
    client.start()

