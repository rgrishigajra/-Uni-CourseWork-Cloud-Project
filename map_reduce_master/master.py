from key_value_pair_cache.client import client
import key_value_pair_cache.helper_functions.log_helper as log_helper
from mapper.mapper import mapper
import os
import configparser
import time
import pickle
import concurrent.futures
from reducer.reducer import reducer


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
            self.LOG.log(50, 'Master dividing file '+file_no)
            with open(file_loc) as doc:
                line = doc.readline()
                while line:
                    if line != '\n':
                        self.assign_mapper(mapper_iterator, file_no, line)
                        mapper_iterator = (
                            mapper_iterator+1) % int(self.config['app_config']['NumberOfMappers'])
                    line = doc.readline()
        self.LOG.log(50, 'Divided all loads successfully')
        return True

    def boot_mappers(self):
        self.LOG.log(50, 'Booting up mappers')
        for mapper_name, mapper_port in self.config['mapper_ports'].items():
            m = mapper(mapper_name, mapper_port)
            # m.get_mapper_data()
            self.mapper_pool.append(self.executor.submit(
                m.get_mapper_data))
        self.LOG.log(50, 'Waiting for mappers')
        concurrent.futures.wait(self.mapper_pool)
        self.LOG.log(50, 'Done for mappers')
        # break
        return True

    def boot_reducers(self):
        id = 0
        self.LOG.log(50, 'Booting up reducers')
        for reducer_name, reducer_port in self.config['mapper_ports'].items():
            r = reducer(reducer_name, reducer_port)
            # r.get_reducer_data()
            self.reducer_pool.append(self.executor.submit(
                r.get_reducer_data))
            # break
        self.LOG.log(50, 'Waiting for reducers')
        concurrent.futures.wait(self.reducer_pool)
        self.LOG.log(50, 'Done for reducers')
        return True

    def get_output(self):
        keys = self.master_client.get_keys("reducer_output")
        self.LOG.log(50, "getting final output from key-value store")
        if not os.path.exists(self.config['app_config']['OutputFile']):
            open(self.config['app_config']['OutputFile'], 'x')
        with open(self.config['app_config']['OutputFile'], 'w') as fd:
            for key in keys:
                data = self.master_client.get_key_lines(key)
                kay_val_split_msg = data.split(' \r\n')
                fd.write(kay_val_split_msg[1])
        self.LOG.log(50, 'final answer dumped into file ' +
                     str(self.config['app_config']['OutputFile']))
        return True

    def create_status_map(self):
        self.LOG.log(50,'creating status map for mappers and reducers')
        for i in range(int(self.config['app_config']['NumberOfMappers'])):
            self.master_client.set_key('mapper_status'+str(i), 'idle')
        for i in range(int(self.config['app_config']['NumberOfReducers'])):
            self.master_client.set_key('reducer_status'+str(i), 'idle')
        return True

    def run_map_reduce(self):
        self.LOG.log(50, "Starting up map-reduce with " +
                     self.config['app_config']['NumberOfMappers']+" mappers and "+self.config['app_config']['NumberOfReducers']+" reducers")
        self.create_status_map()
        self.divide_loads()
        self.boot_mappers()
        self.boot_reducers()
        self.get_output()
        return True

    def __init__(self):
        self.LOG.log(50, "Booting up map-reduce master")
        self.master_client = client(
            int(self.config['app_config']['KeyValueServerPort']))
        self.mapper_pool = []
        self.reducer_pool = []
        self.executor = concurrent.futures.ProcessPoolExecutor()
        # while True:
        #     if not self.master_client.ping_server():
        #         self.LOG.log(50, 'key-value is store offline')
        #         time.sleep(10)
        #     else:
        #         break
        return
