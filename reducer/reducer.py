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


class reducer:
    config = configparser.ConfigParser()
    config.read('config.ini')
    LOG = log_helper._logger("map-reduce reducer")

    def send_reducer_output(self, reducer_output):
        self.LOG.log(50, 'Sending reducer out put for ' +
                     str(self.reducer_id)+" to key value store")
        msg_key = 'reducer_output' + str(self.reducer_id)
        for list_item in reducer_output:
            msg_val = str(list_item[0]+" "+str(list_item[1])+"\n")
            self.reducer_client.append_key(msg_key, msg_val)
        self.LOG.log(50, 'output for reducer ' +
                     str(self.reducer_id) + 'stored in key value store')
        return True

    def run_serialized_reducer(self, input_list):
        self.LOG.log(
            50, 'Running supplied reducer on worker '+str(self.reducer_id))
        with open(self.config['app_config']['ReducerCodeSerialized'], 'rb') as fd:
            code_string = fd.read()
            code = marshal.loads(code_string)
            user_defined_reduce_function = types.FunctionType(
                code, globals(), "user_defined_reducer_function"+str(self.reducer_id))
        reducer_output = user_defined_reduce_function(input_list)
        self.LOG.log(50, 'Reducer '+str(self.reducer_id) +
                     " has run reducer function")
        return reducer_output

    def get_reducer_data(self):
        try:
            keys = self.reducer_client.get_keys("reducer"+str(self.reducer_id))
            data = ''
            for key in keys:
                data = self.reducer_client.get_key_lines(key)
                self.LOG.log(50, "reducer "+str(self.reducer_id) +
                             " received data "+str(len(data)))
                lines = data.split('\n')[1:]
                input_list = []
                # split from lines to list of tuples
                for line in lines:
                    words = line.split()
                    if len(words) == 2:
                        input_list.append((words[0], words[1]))
                self.LOG.log(50, "reducer "+str(self.reducer_id) +
                            " collected these keys data :"+str(len(input_list)))
                # runs serial reducer script
                reducer_output = self.run_serialized_reducer(input_list)
                self.send_reducer_output(reducer_output)
            if random.randrange(int(self.config['app_config']['NumberOfReducers'])+1) ==int(self.config['app_config']['NumberOfReducers']) and self.config['app_config']['TestReducerFail'] == "True":
                self.LOG.log(30,"Creating an exception in reducer "+str(self.reducer_id)+" for testing")
                raise Exception
            self.reducer_client.set_key(
                'reducer_status'+str(self.reducer_id), 'finished')
            return True
        except Exception as e:
            self.LOG.log(30, "Reducer "+str(self.reducer_id)+" broke down")
            return False

    def get_reducer_id(self):
        keys = self.reducer_client.get_keys('reducer_status')
        for key in keys:
            val = self.reducer_client.get_key(key)
            if val.split(' \r\n')[1] == 'idle':
                id = val.split(' \r\n')[0].split()[1][len('reducer_status'):]
                self.reducer_client.set_key(
                    'reducer_status'+str(id), 'assigned')
                return int(id)
        return 99999

    def __init__(self, reducer_name, reducer_port):
        self.reducer_port = reducer_port
        self.reducer_name = reducer_name
        self.reducer_client = client(
            int(self.config['app_config']['KeyValueServerPort']))
        self.reducer_id = self.get_reducer_id()
        self.LOG.log(50, "Booting up map-reduce reducer with id " +
                     str(self.reducer_id))

        # if not self.reducer_client.ping_server():
        #     self.LOG.log(50, 'key-value is store offline')
        #     exit()
        self.LOG.log(50, 'reducer '+str(self.reducer_id)+" intialized")
        # self.map()
        return
