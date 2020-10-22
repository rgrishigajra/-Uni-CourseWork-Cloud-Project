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
from reducer.word_count_reducer import word_count_reducer


class reducer:
    config = configparser.ConfigParser()
    config.read('config.ini')
    LOG = log_helper._logger("map-reduce reducer")

    def send_reducer_output(self, reducer_output):
        try:
            self.LOG.log(50, 'Sending reducer out put for ' +
                         str(self.reducer_id)+" to key value store")
            msg_key = 'reducer_output' + str(self.reducer_id)
            for list_item in reducer_output:
                msg_val = str(list_item[0]+" "+str(list_item[1])+"\n")
                self.reducer_client.append_key(msg_key, msg_val)
            self.LOG.log(50, 'output for reducer ' +
                         str(self.reducer_id) + 'stored in key value store')
            return True
        except Exception as e:
            self.LOG.log(30, "Exception while running send_reducer_output")
            print(e, sys.exc_info())

    def run_serialized_reducer(self, input_list):
        try:
            self.LOG.log(
                50, 'Running supplied reducer on worker '+str(self.reducer_id))
            # with open(self.config['app_config']['ReducerCodeSerialized'], 'rb') as fd:
            #     code_string = fd.read()
            #     code = marshal.loads(code_string)
            #     user_defined_reduce_function = types.FunctionType(
            #         code, globals(), "user_defined_reducer_function"+str(self.reducer_id))
            reducer_output = word_count_reducer(input_list)
            # reducer_output = user_defined_reduce_function(input_list)
            self.LOG.log(50, 'Reducer '+str(self.reducer_id) +
                         " has run reducer function")
            return reducer_output
        except Exception as e:
            self.LOG.log(30, "Exception while running run_serialized_reducer")
            print(e, sys.exc_info())

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
            if random.randrange(int(self.config['app_config']['NumberOfReducers'])+1) == int(self.config['app_config']['NumberOfReducers']) and self.config['app_config']['TestReducerFail'] == "True":
                self.LOG.log(30, "Creating an exception in reducer " +
                             str(self.reducer_id)+" for testing")
                raise Exception
            self.finished_checker = False
            self.reducer_client.set_key(
                'reducer_status'+str(self.reducer_id), 'finished')
            return True
        except Exception as e:
            self.LOG.log(30, "Exception while running get_reducer_data")
            print(e, sys.exc_info())
            self.LOG.log(50, "Reducer "+str(self.reducer_id)+" broke down")
            return False

    def get_reducer_id(self):
        # keys = self.reducer_client.get_keys('reducer_status')
        # for key in keys:
        #     val = self.reducer_client.get_key(key)
        #     if val.split(' \r\n')[1] == 'idle':
        #         id = val.split(' \r\n')[0].split()[1][len('reducer_status'):]
        req = urllib.request.Request(
            'http://metadata.google.internal/computeMetadata/v1/instance/hostname', headers={"Metadata-Flavor": "Google"})
        host_name = urllib.request.urlopen(req).read().decode().split('.')
        # host_name = ['reducer0', 'c', 'rishabh-gajra', 'internal']
        id = host_name[0][len('reducer'):]
        self.reducer_client.set_key(
            'reducer_status'+str(id), 'assigned')
        return int(id)

    def send_heartbeat(self):
        while self.finished_checker:
            self.reducer_client.set_key(
                'reducer_status'+str(self.reducer_id), 'assigned')
            time.sleep(7)
        return True

    def reducer_clean_files(self):
        self.LOG.log(
            50, 'Cleaning previous files for reducer %d' % (self.reducer_id))
        msg_key = 'reducer_output' + str(self.reducer_id)
        self.reducer_client.clean_file_by_line(msg_key)
        return True

    def __init__(self, reducer_name, reducer_port):
        self.finished_checker = True
        self.reducer_port = reducer_port
        self.reducer_name = reducer_name
        self.reducer_client = client(str(self.config['app_config']['KeyValueServerIP']),
                                     int(self.config['app_config']['KeyValueServerPort']))
        self.reducer_id = self.get_reducer_id()
        heartbeat_thread = threading.Thread(
            target=self.send_heartbeat, args=(), daemon=True)
        heartbeat_thread.start()
        self.reducer_clean_files()
        self.LOG.log(50, "Booting up map-reduce reducer with id " +
                     str(self.reducer_id))

        # if not self.reducer_client.ping_server():
        #     self.LOG.log(50, 'key-value is store offline')
        #     exit()
        self.LOG.log(50, 'reducer '+str(self.reducer_id)+" intialized")
        # self.map()
        return
