from key_value_pair_cache.client import client
import key_value_pair_cache.helper_functions.log_helper as log_helper
import configparser
import os
import sys
from collections import defaultdict
import marshal
import types
import re
from key_value_pair_cache.helper_functions.hash_fnv1a import fnv1a_32
import random
import urllib.request
import threading
import time
from mapper.word_count_mapper import word_count_mapper


class mapper:
    config = configparser.ConfigParser()
    config.read('config.ini')
    LOG = log_helper._logger("map-reduce mapper")

    def send_mapper_output(self, mapper_output):
        self.LOG.log(50, 'Sending mapper out put for ' +
                     str(self.mapper_id)+" to key value store")
        for list_item in mapper_output:
            # hashing to assign to a reducer
            reducer_id = int(fnv1a_32(list_item[0])) % int(
                (self.config['app_config']['NumberOfReducers']))
            msg_key = "reducer"+str(reducer_id)+"mapper"+str(self.mapper_id)
            msg_val = str(list_item[0]+" "+str(list_item[1])+"\n")
            self.mapper_client.append_key(msg_key, msg_val)
        self.LOG.log(50, 'output for mapper ' +
                     str(self.mapper_id) + ' stored in key value store')
        return True

    def run_serialized_mapper(self, key, value):
        self.LOG.log(
            50, 'Running supplied mapper on worker '+str(self.mapper_id))
        # with open(self.config['app_config']['MapperCodeSerialized'], 'rb') as fd:
        #     code_string = fd.read()
        #     code = marshal.loads(code_string)
        #     user_defined_map_function = types.FunctionType(
        #         code, globals(), "user_defined_map_function"+str(self.mapper_id))
        # mapper_output = user_defined_map_function(key, value)
        mapper_output = word_count_mapper(key, value)
        self.LOG.log(50, 'Mapper '+str(self.mapper_id) +
                     " has run mapper function")
        return mapper_output

    def get_mapper_data(self):
        try:
            # self.mapper_id = self.mapper_client.get_assignment(
            #     self.mapper_name, self.mapper_port)
            keys = self.mapper_client.get_keys("mapper"+str(self.mapper_id))
            data = []
            for key in keys:
                data = self.mapper_client.get_key_lines(key)
                self.LOG.log(50, "mapper "+str(self.mapper_id) +
                             " received data "+str(len(data)))
                kay_val_split_msg = data.split(' \r\n')
                key_value_pair = [data.split(' \r\n')[0].split(
                    ' ')[1][len("mapper"+str(self.mapper_id)):]]
                key_value_pair.append(kay_val_split_msg[1])
                # runs serial mapper script
                mapper_output = self.run_serialized_mapper(
                    key_value_pair[0], key_value_pair[1])
                # gets a list of (key,value) pairs, storing it in kay value store for each reducer
                self.send_mapper_output(mapper_output)
            if random.randrange(int(self.config['app_config']['NumberOfMappers'])+1) == int(self.config['app_config']['NumberOfMappers']) and self.config['app_config']['TestMapperFail'] == "True":
                self.LOG.log(30, "Creating an exception in mapper " +
                             str(self.mapper_id)+" for testing")
                raise Exception
            self.finished_checker = False
            self.mapper_client.set_key(
                'mapper_status'+str(self.mapper_id), 'finished')
            self.LOG.log(50, 'mapper '+str(self.mapper_id)+" done")
            return True
        except Exception as e:
            self.LOG.log(30, "Mapper "+str(self.mapper_id)+" broke down")
            self.LOG.log(30, e)
            return False

    def get_mapper_id(self):
        # keys = self.mapper_client.get_keys('mapper_status')
        req = urllib.request.Request(
            'http://metadata.google.internal/computeMetadata/v1/instance/hostname', headers={"Metadata-Flavor": "Google"})
        host_name = urllib.request.urlopen(req).read().decode().split('.')
        # host_name = ['mapper0', 'c', 'rishabh-gajra', 'internal']
        id = host_name[0][len('mapper'):]
        self.mapper_client.set_key('mapper_status'+str(id), 'assigned')
        return int(id)

    def send_heartbeat(self):
        while self.finished_checker:
            self.mapper_client.set_key(
                'mapper_status'+str(self.id), 'assigned')
            time.sleep(7)
        return True

    def __init__(self, mapper_name, mapper_port):
        self.finished_checker = True
        self.mapper_port = mapper_port
        self.mapper_name = mapper_name
        self.mapper_client = client(str(self.config['app_config']['KeyValueServerIP']),
                                    int(self.config['app_config']['KeyValueServerPort']))
        self.mapper_id = self.get_mapper_id()
        heartbeat_thread = threading.Thread(
            target=self.send_heartbeat, args=())
        heartbeat_thread.start()
        # self.send_heartbeat()
        self.LOG.log(50, "Booting up map-reduce mapper with id " +
                     str(self.mapper_id))

        # if not self.mapper_client.ping_server():
        #     self.LOG.log(50, 'key-value is store offline')
        #     exit()
        self.LOG.log(50, 'mapper '+str(self.mapper_id)+" intialized")
        # self.map()
        return
