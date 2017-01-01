import argparse
import datetime
import json

import pymongo
import redis
from components.lib import common_utils
from components.lib import tester


def main():
    server = None
    mongo_db = "pritesterdb"
    mongo_db_collection = "pri_status_collection"
    mongo_client = pymongo.MongoClient("localhost", 27017)
    redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
    parser_obj = argparse.ArgumentParser(description="parse me may be!!")
    parser_obj.add_argument('--server',
                            '-s',
                            dest='server',
                            action='store',
                            type=str,
                            default=None
                            )

    parser_obj.add_argument('--testing-mode',
                            '-t',
                            dest='testing_mode',
                            action='store',
                            type=str,
                            default=None
                            )
    parsed_args = parser_obj.parse_args()
    server = parsed_args.server
    testing_mode = parsed_args.testing_mode

    if testing_mode == "true":
        pri_tester_obj = tester.PRITester(server=server,
                                          testing=True)
    else:
        pri_tester_obj = tester.PRITester(server=server)

    pri_tester_obj.get_server_details()
    lower_functional = pri_tester_obj.get_functional_pris(pri_tester_obj.lower_port)
    upper_functional = pri_tester_obj.get_functional_pris(pri_tester_obj.upper_port)

    server_level_info = pri_tester_obj.pri_info_document
    server_level_info["ipaddr_private"] = server
    server_level_info["ipaddr_public"] = pri_tester_obj.server_public_address
    server_level_info["hostname"] = pri_tester_obj.server_host_name

    cursor = mongo_client["pritesterdb"]["pri_status_collection"].find({"ipaddr_private": server})
    if cursor.count() > 0:
        server_level_info["epoch_updated"] = common_utils.CommonMethods.datetime_to_epoch(datetime.datetime.now())
    else:
        server_level_info["epoch_added"] = common_utils.CommonMethods.datetime_to_epoch(datetime.datetime.now())

    for pri in lower_functional:
        response = pri_tester_obj.dial_individual_pri(pri, pri_tester_obj.lower_port)
        print response
        current_wanpipe = "wp" + str(pri)
        current_wanpipe_dict = {current_wanpipe: {}}
        wanpipe_level_info = tester.PRITester.wanpipe_info_document

        if "fs_sim" in response:
            if response[1] == "SUCCESS":
                wanpipe_level_info["physical"] = "true"
                wanpipe_level_info["signalling"] = "true"
                wanpipe_level_info["outgoing"] = "true"
                current_wanpipe_dict[current_wanpipe] = wanpipe_level_info
            else:
                wanpipe_level_info["physical"] = "false"
                wanpipe_level_info["signalling"] = "false"
                wanpipe_level_info["outgoing"] = "false"
                current_wanpipe_dict[current_wanpipe] = wanpipe_level_info

        if response[1].find("NORMAL_CLEARING") != -1:
            wanpipe_level_info["physical"] = "true"
            wanpipe_level_info["signalling"] = "true"
            wanpipe_level_info["outgoing"] = "true"
            current_wanpipe_dict[current_wanpipe] = wanpipe_level_info

        else:
            wanpipe_level_info["physical"] = "false"
            wanpipe_level_info["signalling"] = "false"
            wanpipe_level_info["outgoing"] = "false"
            wanpipe_level_info["outgoing_caller_id"] = ""
            wanpipe_level_info["hangup_cause"] = response[1]
            current_wanpipe_dict[current_wanpipe] = wanpipe_level_info
        redis_client.publish("outgoing", json.dumps(current_wanpipe_dict))

    for pri in upper_functional:

        response = pri_tester_obj.dial_individual_pri(pri, pri_tester_obj.upper_port)
        print response
        current_wanpipe = "wp" + str(pri)
        current_wanpipe_dict = {current_wanpipe: {}}
        wanpipe_level_info = tester.PRITester.wanpipe_info_document

        if "fs_sim" in response:
            if response[1] == "SUCCESS":
                wanpipe_level_info["physical"] = "true"
                wanpipe_level_info["signalling"] = "true"
                wanpipe_level_info["outgoing"] = "true"
                current_wanpipe_dict[current_wanpipe] = wanpipe_level_info
            else:
                wanpipe_level_info["physical"] = "false"
                wanpipe_level_info["signalling"] = "false"
                wanpipe_level_info["outgoing"] = "false"
                current_wanpipe_dict[current_wanpipe] = wanpipe_level_info

        elif response[1].find("NORMAL_CLEARING") != -1:
            wanpipe_level_info["physical"] = "true"
            wanpipe_level_info["signalling"] = "true"
            wanpipe_level_info["outgoing"] = "true"
            current_wanpipe_dict["wanpipe"][current_wanpipe] = wanpipe_level_info
            # redis_client.publish("outgoing", json.dumps(server_level_info))
        else:
            wanpipe_level_info["physical"] = "false"
            wanpipe_level_info["signalling"] = "false"
            wanpipe_level_info["outgoing"] = "false"
            wanpipe_level_info["outgoing_caller_id"] = ""
            wanpipe_level_info["hangup_cause"] = response[1]
            current_wanpipe_dict[current_wanpipe] = wanpipe_level_info
        redis_client.publish("outgoing", json.dumps(current_wanpipe_dict))
    wanpipe = {}
    for i in range(len(redis_client.smembers(pri_tester_obj.redis_wanpipe_key))):
        individual_wanpipe = redis_client.spop(pri_tester_obj.redis_wanpipe_key)
        individual_wanpipe = eval(individual_wanpipe)
        wanpipe[individual_wanpipe.keys()[0]] = individual_wanpipe[individual_wanpipe.keys()[0]]
    server_level_info["wanpipe"] = wanpipe
    cursor = mongo_client["pritesterdb"]["pri_status_collection"].update(
         {
             "ipaddr_private": pri_tester_obj.server
         }, {"$set": server_level_info}, upsert=True
     )
    print cursor



if __name__ == '__main__':
    main()
