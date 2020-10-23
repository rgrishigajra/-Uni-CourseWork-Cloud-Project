from socket import *
import string
import random
import key_value_pair_cache.helper_functions.log_helper as log_helper
import os
import random


class client:
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
    LOG = log_helper._logger("client")

    def clean_file_by_line(self, key):
        client_message = 'clean '+key+' \r\n'
        self.client_socket.send(client_message.encode())
        self.LOG.log(20, 'Client sent a cleans request!')
        server_output = self.client_socket.recv(4096)
        self.LOG.log(10, server_output)
        return server_output.decode()

    def delete_all(self):
        try:
            client_message = 'delete all \r\n'
            self.client_socket.send(client_message.encode())
            self.LOG.log(20, 'Client sent a get request!')
            server_output = self.client_socket.recv(4096)
            return server_output.decode()
        except ConnectionRefusedError as e:
            self.LOG.exception(e)
        return

    def append_key(self, key, value):
        try:
            client_message = 'append ' + key + ' ' + \
                str(len(value.encode()))+' \r\n' + value + '\r\n'
            self.client_socket.send(client_message.encode())
            self.LOG.log(10, 'Client sent a append request!')
            server_output = self.client_socket.recv(4096)
            self.LOG.log(10, server_output)
            return server_output.decode()
        except ConnectionRefusedError as e:
            self.LOG.exception(e)
# sends key, value to the server in required format

    def set_key(self, key, value):
        try:
            client_message = 'set ' + key + ' ' + \
                str(len(value.encode()))+' \r\n' + value + '\r\n'
            self.client_socket.send(client_message.encode())
            self.LOG.log(10, 'Client sent a set request!')
            server_output = self.client_socket.recv(4096)
            self.LOG.log(10, server_output)
            return server_output.decode()
        except ConnectionRefusedError as e:
            self.LOG.exception(e)

    def get_assignment(self, mapper_name, mapper_port):
        return 0

    def get_keys(self, id):
        try:
            client_message = 'searchid' + ' ' + str(id)+" \r\n"
            self.client_socket.send(client_message.encode())
            self.LOG.log(10, 'Client sent a set request!')
            server_output = self.client_socket.recv(4096)
            self.LOG.log(10, server_output)
            # returns a list of keys
            return server_output.decode().split(' \r\n')[1].split(' ')[:-1]
        except ConnectionRefusedError as e:
            self.LOG.exception(e)

    def get_key_lines(self, key):
        try:
            client_message = 'getlines '+key+' \r\n'
            self.client_socket.send(client_message.encode())
            self.LOG.log(20, 'Client sent a get lines for %s request!' % (key))
            server_output = self.client_socket.recv(4096)
            decoded_msg = server_output.decode()
            self.LOG.log(20, 'Client got  %s ' % (decoded_msg))
            # if decoded_msg[len(decoded_msg)-len('END\r\n'):] == 'END\r\n':
            #     return decoded_msg
            value_len = len(server_output)
            value_len_given_by_server = int(decoded_msg.split(' ')[2])
            self.LOG.log(20, 'Get lines left for request: %d - %d' %
                         (value_len_given_by_server, value_len))
            while value_len_given_by_server > value_len:
                server_output += self.client_socket.recv(
                    min(4096, value_len_given_by_server-value_len))
                value_len += min(4096, value_len_given_by_server-value_len)
            decoded_msg = server_output.decode("utf-8", "ignore")
            return decoded_msg
        except Exception as e:
            self.LOG.exception(e)
            print(e)
        return 'VALUE error 20 \r\nerror \r\nEND\r\n'
# sends a get request by sending a key in required format

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

# generates a random key of random length upto max_key and random value upto random length or max_value.
# does a set and a get with them
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

    def ping_server(self):
        self.LOG.log(10, 'pinging server')
        self.client_socket.send('ping \r\n'.encode())
        server_output = self.client_socket.recv(4096)
        if (server_output.decode() == "ONLINE\r\n"):
            return True
        return False

    def close_client(self):
        self.client_socket.close()
        return True

    def __init__(self, ip, port_num):
        while True:
            try:
                server_name = ip
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
