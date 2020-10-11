from key_value_pair_cache.client import client
import key_value_pair_cache.helper_functions.log_helper as log_helper
from mapper.mapper import mapper
import os
import configparser
import time
import pickle


class map_reduce:
    config = configparser.ConfigParser()
    config.read('config.ini')
    LOG = log_helper._logger("map-reduce master")

    def assign_mapper(self, mapper_number, file_name, value):
        return self.master_client.append_key("mapper"+str(mapper_number)+file_name, value)

    def divide_loads(self):
        load = []
        for file_no, file_loc in self.config['input_files'].items():
            mapper_iterator = 0
            with open(file_loc) as doc:
                line = doc.readline()
                while line:
                    if line != '\n':
                        self.assign_mapper(mapper_iterator, file_no, line)
                        mapper_iterator = (
                            mapper_iterator+1) % int(self.config['app_config']['NumberOfMappers'])
                    line = doc.readline()
        return True

    def boot_mappers(self):
        for mapper_name, mapper_port in self.config['mapper_ports'].items():
            m = mapper(mapper_name, mapper_port)
            break
        return True

    def run_map_reduce(self):
        self.LOG.log(50, "Starting up map-reduce with ")
        # self.divide_loads()
        self.boot_mappers()
        None
        return True

    def __init__(self):
        self.LOG.log(50, "Booting up map-reduce master")
        self.master_client = client(
            int(self.config['app_config']['KeyValueServerPort']))
        # while True:
        #     if not self.master_client.ping_server():
        #         self.LOG.log(50, 'key-value is store offline')
        #         time.sleep(10)
        #     else:
        #         break
        return
