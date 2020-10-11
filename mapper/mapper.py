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


class mapper:
    config = configparser.ConfigParser()
    config.read('config.ini')
    LOG = log_helper._logger("map-reduce mapper")

    def send_mapper_output(self, mapper_output):
        for list_item in mapper_output:
            # hashing to assign to a reducer
            reducer_id = int(fnv1a_32(list_item[0])) % int(
                (self.config['app_config']['NumberOfReducers']))
            msg_key = "reducer"+str(reducer_id)+"mapper"+str(self.mapper_id)
            msg_val = str(list_item[0]+" "+str(list_item[1])+"\n")
            self.mapper_client.append_key(msg_key, msg_val)
        return True

    def run_serialized_mapper(self, key, value):
        self.LOG.log(
            20, 'Running supplied mapper on worker '+str(self.mapper_id))
        with open(self.config['app_config']['MapperCodeSerialized'], 'rb') as fd:
            code_string = fd.read()
            code = marshal.loads(code_string)
            user_defined_map_function = types.FunctionType(
                code, globals(), "user_defined_map_function")
            mapper_output = user_defined_map_function(key, value)
        return mapper_output

    def get_mapper_data(self):
        self.mapper_id = self.mapper_client.get_assignment(
            self.mapper_name, self.mapper_port)
        keys = self.mapper_client.get_mapper_keys(self.mapper_id)
        data = []
        for key in keys:
            data = self.mapper_client.get_key_lines(key)
            self.LOG.log(20, "mapper "+str(self.mapper_id) +
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
            break
        return True

    def __init__(self, mapper_name, mapper_port):
        self.mapper_port = mapper_port
        self.mapper_name = mapper_name
        self.LOG.log(50, "Booting up map-reduce mapper")
        self.mapper_client = client(
            int(self.config['app_config']['KeyValueServerPort']))
        # if not self.mapper_client.ping_server():
        #     self.LOG.log(50, 'key-value is store offline')
        #     exit()
        self.get_mapper_data()
        # self.map()
        return
