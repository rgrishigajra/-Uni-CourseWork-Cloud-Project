from key_value_pair_cache.client import client
import key_value_pair_cache.helper_functions.log_helper as log_helper
import os
import configparser
import time
import pickle
import concurrent.futures
from collections import defaultdict
import subprocess


class map_reduce:
    config = configparser.ConfigParser()
    config.read('config.ini')
    LOG = log_helper._logger("map-reduce master")

    def assign_mapper(self, mapper_number, file_name, value):
        return self.master_client.append_key("mapper"+str(mapper_number)+file_name, value)

    def create_status_map(self):
        self.LOG.log(50, 'creating status map for mappers and reducers')
        for i in range(int(self.config['app_config']['NumberOfMappers'])):
            self.master_client.set_key('mapper_status'+str(i), 'idle')
        for i in range(int(self.config['app_config']['NumberOfReducers'])):
            self.master_client.set_key('reducer_status'+str(i), 'idle')
        return True

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

    def boot_instance(self, instance_name, startup_script):
        command = "gcloud compute instances create %s --zone us-central1-a --machine-type=e2-micro --image=ubuntu-1804-bionic-v20201014 --image-project=ubuntu-os-cloud --boot-disk-size=10GB --scopes=compute-rw,storage-ro --metadata-from-file startup-script=%s" % (
            instance_name, startup_script)
        try:
            subprocess.run(command, shell=True, check=True)
        except Exception as e:
            self.LOG.log(50, 'exception while booting instance %s' %
                         (instance_name))
            self.LOG.log(30, e)
        return True

    def delete_instance(self, instance_name):
        command = "gcloud compute instances delete %s  --zone us-central1-a --quiet" % (
            instance_name)
        try:
            subprocess.run(command, shell=True, check=True)
        except Exception as e:
            self.LOG.log(50, 'exception while deleting instance %s' %
                         (instance_name))
            self.LOG.log(30, e)
        return True

    def boot_mappers(self):
        self.LOG.log(50, 'Booting up mappers')
        for i in range(int(self.config['app_config']['NumberOfMappers'])):
            self.boot_instance('mapper'+str(i), 'mapper_starter.sh')
            # subprocess.run("python3 mapper_init.py",
            #                shell=True, check=True)
            # m = mapper('', '')  # for ip and port number in future
            # # m.get_mapper_data()
            # self.mapper_pool.append(self.executor.submit(
            #     m.get_mapper_data))
        self.LOG.log(50, 'Waiting for mappers')
        # concurrent.futures.wait(self.mapper_pool)
        return True

    def moniter_mappers(self):
        # try:
        no_of_loops = 0
        while no_of_loops < 100:
            time.sleep(23)
            no_of_loops += 1
            status_dict = defaultdict(str)
            total_dict = defaultdict(int)
            self.LOG.log(
                50, 'master checking mapper health, heartbeat:' + str(no_of_loops))
            keys = self.master_client.get_keys('mapper_status')
            # print('key', keys)
            for key in keys:
                val = self.master_client.get_key(key)
                status_dict[key] = val.split(' \r\n')[1]
                # print(key, status_dict[key])
                total_dict[val.split(' \r\n')[1]] += 1
            self.LOG.log(50, 'idle:' + str(total_dict['idle'])+' assigned:' +
                         str(total_dict['assigned'])+' check:' + str(total_dict['check'])+' finished:'+str(total_dict['finished']))
            if total_dict['finished'] == int(self.config['app_config']['NumberOfMappers']):
                break
            for running_mapper in status_dict.keys():
                if status_dict[running_mapper] == 'check':
                    self.LOG.log(50, 'Master found mapper %s inactive, booting new instance' %
                                 (running_mapper[len(running_mapper)-1:]))
                    self.master_client.set_key(running_mapper, 'idle')
                    self.delete_instance(
                        'mapper'+running_mapper[len(running_mapper)-1:])
                    self.boot_instance(
                        'mapper'+running_mapper[len(running_mapper)-1:], 'mapper_starter.sh')
                    # break
                if status_dict[running_mapper] == 'assigned':
                    self.LOG.log(50, 'Master found mapper %s is alive, waiting for it to finish' %
                                 (running_mapper[len(running_mapper)-1:]))
                    self.master_client.set_key(running_mapper, 'check')
                if status_dict[running_mapper] == 'idle':
                    self.LOG.log(50, 'Master found mapper % s idle, waiting for it to boot up' %
                                 (running_mapper[len(running_mapper)-1:]))
        # except Exception as e:
        #     self.LOG.log(30, e)
        self.LOG.log(50, 'Done for mappers')
        return True

    def delete_mappers(self):
        for i in range(int(self.config['app_config']['NumberOfMappers'])):
            self.delete_instance('mapper'+str(i))
        return True

    def boot_reducers(self):
        id = 0
        self.LOG.log(50, 'Booting up reducers')
        for i in range(int(self.config['app_config']['NumberOfReducers'])):
            self.boot_instance('reducer'+str(i), 'reducer_starter.sh')
            # subprocess.run("python3 reducer_init.py",
            #                shell=True, check=True)
            # r = reducer('', '')  # for ip and port numbers in future
            # # r.get_reducer_data()
            # self.reducer_pool.append(self.executor.submit(
            #     r.get_reducer_data))
            # break
        self.LOG.log(50, 'Waiting for reducers')
        # concurrent.futures.wait(self.reducer_pool)
        return True

    def moniter_reducers(self):
        # try:
        no_of_loops = 0
        while no_of_loops < 50:
            time.sleep(23)
            no_of_loops = 1
            status_dict = defaultdict(str)
            total_dict = defaultdict(int)
            self.LOG.log(
                50, 'master checking reducer health, heartbeat:' + str(no_of_loops))
            keys = self.master_client.get_keys('reducer_status')
            # print('keys', keys)
            for key in keys:
                val = self.master_client.get_key(key)
                status_dict[key] = val.split(' \r\n')[1]
                # print(key, status_dict[key])
                total_dict[val.split(' \r\n')[1]] += 1
            self.LOG.log(50, 'idle:' + str(total_dict['idle'])+' assigned:' +
                         str(total_dict['assigned'])+' check:' + str(total_dict['check'])+' finished:'+str(total_dict['finished']))
            if total_dict['finished'] == int(self.config['app_config']['NumberOfReducers']):
                break
            for running_reducer in status_dict.keys():
                if status_dict[running_reducer] == 'check':
                    self.LOG.log(50, 'Master found reducer %s inactive, booting new instance' %
                                 (running_reducer[len(running_reducer)-1:]))
                    self.master_client.set_key(running_reducer, 'idle')
                    self.delete_instance(
                        'reducer'+running_reducer[len(running_reducer)-1:])
                    self.boot_instance(
                        'reducer'+running_reducer[len(running_reducer)-1:], 'reducer_starter.sh')
                    # break
                if status_dict[running_reducer] == 'assigned':
                    self.LOG.log(50, 'Master found reducer %s is alive, waiting for it to finish' %
                                 (running_reducer[len(running_reducer)-1:]))
                    self.master_client.set_key(running_reducer, 'check')
                if status_dict[running_reducer] == 'idle':
                    self.LOG.log(50, 'Master found reducer % s idle, waiting for it to boot up' %
                                 (running_reducer[len(running_reducer)-1:]))
        # except Exception as e:
        #     self.LOG.log(30, e)
        self.LOG.log(50, 'Done for reducers')
        return True

    def delete_reducers(self):
        for i in range(int(self.config['app_config']['NumberOfReducers'])):
            self.delete_instance('reducer'+str(i))
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
                # if len(kay_val_split_msg) > 1:
                fd.write(kay_val_split_msg[1])
        self.LOG.log(50, 'final answer dumped into file ' +
                     str(self.config['app_config']['OutputFile']))
        return True

    def run_map_reduce(self):
        self.LOG.log(50, "Starting up map-reduce with " +
                     self.config['app_config']['NumberOfMappers']+" mappers and "+self.config['app_config']['NumberOfReducers']+" reducers")
        # self.create_status_map()
        # self.divide_loads()
        self.boot_mappers()
        # self.moniter_mappers()
        # self.delete_mappers()
        # self.boot_reducers()
        # self.moniter_reducers()
        # self.delete_reducers()
        # self.get_output()
        return True

    def get_server_ip(self):
        output = subprocess.run(
            "gcloud compute instances describe key-value-server4 --zone=us-central1-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)'", shell=True, check=True, stdout=subprocess.PIPE)
        ip = output.stdout.decode()[:-1]
        return ip

    def __init__(self):
        self.LOG.log(50, "Booting up map-reduce master")
        self.key_value_ip = str(self.get_server_ip())
        self.master_client = client(self.key_value_ip, int(
            self.config['app_config']['KeyValueServerPort']))
        self.mapper_pool = []
        self.reducer_pool = []
        self.executor = concurrent.futures.ProcessPoolExecutor()
        self.master_client.delete_all()
        self.master_client.set_key(
            'NumberOfMappers', self.config['app_config']['NumberOfMappers'])
        self.master_client.set_key(
            'NumberOfReducers', self.config['app_config']['NumberOfReducers'])
        self.master_client.set_key(
            'MapperCodeSerialized', self.config['app_config']['MapperCodeSerialized'])
        self.master_client.set_key(
            'ReducerCodeSerialized', self.config['app_config']['ReducerCodeSerialized'])
        self.master_client.set_key(
            'TestMapperFail', self.config['app_config']['TestMapperFail'])
        self.master_client.set_key(
            'TestReducerFail', self.config['app_config']['TestReducerFail'])
        return
