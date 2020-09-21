from socket import *
import string
import random
import helper_functions.log_helper
import os
import random


class client:
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
    LOG = helper_functions.log_helper._logger("client")

#sends key, value to the server in required format
    def set_key(self, key, value):
        try:
            client_message = 'set ' + key + ' ' + \
                str(len(value.encode()))+' \r\n' + value + '\r\n'
            self.client_socket.send(client_message.encode())
            self.LOG.log(20, 'Client sent a set request!')
            server_output = self.client_socket.recv(4096)
            self.LOG.log(10, server_output)
            return server_output.decode()
        except ConnectionRefusedError as e:
            self.LOG.exception(e)

#sends a get request by sending a key in required format
    def get_key(self, key):
        try:
            client_message = 'get '+key+' \r\n'
            self.client_socket.send(client_message.encode())
            self.LOG.log(20, 'Client sent a get request!')
            server_output = self.client_socket.recv(4096)
            # self.LOG.log(10, server_output)
            return server_output.decode()
        except ConnectionRefusedError as e:
            self.LOG.exception(e)

#generates a random key of random length upto max_key and random value upto random length or max_value. 
#does a set and a get with them
    def spawn_random_client(self, max_key, max_value):
        try:
            key = ''.join(random.choice(string.ascii_lowercase)
                          for i in range(random.randint(1, max_key)))
            value = ''.join(random.choice(string.ascii_lowercase)
                            for i in range(random.randint(1, max_value)))
            self.set_key(key, value)
            get_output = self.get_key(key).split(' ')
            self.close_client()
            if get_output[3].replace('\r\n', '') == value:
                self.LOG.log(
                    20, 'Client got back the same value for key successfully')
                return True
            else:
                self.LOG.log(
                    20, 'Client failed to get back the value for the key')
                return False
        except ConnectionRefusedError as e:
            self.LOG.exception(e)

    def close_client(self):
        self.client_socket.close()
        return True

    def __init__(self, port_num):
        while True:
            try:
                server_name = ""
                server_port = port_num
                self.client_socket = socket(AF_INET, SOCK_STREAM)
                self.client_socket.connect((server_name, server_port))
                break
            except ConnectionRefusedError as e:
                self.LOG.exception(e)

        '''
        uncomment the lines below to run just one client file from command line as client.py with (port number as argument)
        '''
        # key = ''.join(random.choice(string.ascii_lowercase)
        #               for i in range(random.randint(1, 10)))
        # value = ''.join(random.choice(string.ascii_lowercase)
        #                 for i in range(random.randint(1, 100)))
        # result = self.spawn_random_client(key, value)
        # self.close_client()
        return


# client(1028)
