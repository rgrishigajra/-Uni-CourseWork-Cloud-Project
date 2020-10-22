from socket import *
import sys
import os
import key_value_pair_cache.helper_functions.log_helper as log_helper
from key_value_pair_cache.helper_functions.hash_fnv1a import fnv1a_32
import threading
import pickle
import shutil
import json
import configparser


class server:
    values_path = os.path.join(sys.path[0], "values")
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
    map_file_name = os.path.join(sys.path[0], "map_key_to_file")
    function_to_arg_map = {
        "set": "set_key_value",
        "get": "get_key_value",
        "delete": "delete_full_cache",
        "ping": "check_status",
        "append": "append_key_value",
        "searchid": 'search_keys_by_value',
        "getlines": "get_lines_keys_value"
    }
    LOG = log_helper._logger("key-value server")
    key_value = {}
    file_value = {}

    def check_status(self, message_args):
        return "ONLINE\r\n"
        # deletes the entire map(even the persistent version, along with individual value files)

    def delete_full_cache(self, message_args):
        self.LOG.log(50, "You deleted the whole Cache!, starting fresh")
        try:
            shutil.rmtree(self.values_path)
            os.mkdir(self.values_path)
            os.remove(self.map_file_name)
        except (FileExistsError, FileNotFoundError):
            None
        return "DELETED\r\n"

    def search_keys_by_value(self, message_args):
        self.LOG.log(10, "searching keys with "+message_args[1]+" id")
        l = ''
        for key in self.key_value.keys():
            if message_args[1] == key[:len(message_args[1])]:
                l += (key+' ')
        resp = 'KEYS ' + str(len(l.encode())) + \
            ' \r\n' + str(l)+' \r\n' + "END\r\n"
        return resp

# Adds map[key] as file_name in the run time map dumping the latest map to file.
    def add_key_to_map(self, file_name, key):
        self.key_value[key] = file_name
        map_file_lock = threading.Lock()
        map_file_lock.acquire()
        fd = os.open(self.map_file_name, os.O_RDWR | os.O_CREAT)
        fd_obj = os.fdopen(fd, 'wb')
        pickle.dump(self.key_value, fd_obj, protocol=pickle.HIGHEST_PROTOCOL)
        fd_obj.close()
        map_file_lock.release()
        self.LOG.log(10, key[:10]+"... key added to map and dumped to disc!")
        return True

# Loads the map thats been stored before. Automatically called on boot up of the server.
    def read_map_from_disc(self):
        if os.path.exists(self.map_file_name):
            with open(self.map_file_name, 'rb') as handle:
                try:
                    b = pickle.load(handle)
                    if isinstance(b, dict):
                        self.key_value = b.copy()
                    self.LOG.log(10, "map was loaded from disc!")
                    return True
                except EOFError:
                    self.LOG.log(50, "map file had EOF error, starting fresh!")
                    self.delete_full_cache('')
        self.key_value = {}
        open(self.map_file_name, 'x')
        self.LOG.log(50, "New map was loaded from disc!")
        return True

# helper function to create a file named file_name and with the data_block it needs to store.
    def dump_to_file(self, file_name, data_block):
        self.file_value[file_name] = data_block
        fd = os.open(os.path.join(self.values_path, file_name),
                     os.O_RDWR | os.O_CREAT)
        fd_obj = os.fdopen(fd, 'wb')
        pickle.dump(data_block, fd_obj, protocol=pickle.HIGHEST_PROTOCOL)
        fd_obj.close()
        self.LOG.log(10, file_name[:10]+"... file was dumped to disc!")
        return True

    def append_line_to_file(self, file_name, data_block):
        # get exclusive access to the file while appending
        # exec(file_name + " = threading.Lock()")
        # exec(file_name + ".acquire(blocking=True, timeout=-1)")
        with open(os.path.join(self.values_path, file_name), "a") as doc:
            doc.write(data_block)
        self.LOG.log(10, file_name[:10]+"... file had line appended to disc!")
        # exec(file_name + ".release()")
        return True
# function to set the value for a key in persistent store

    def set_key_value(self, message_args):
        self.LOG.log(20, "client fired a set query!")
        try:
            if message_args[1] in self.key_value:  # check if key is present already
                self.dump_to_file(
                    self.key_value[message_args[1]], message_args[3].replace('\r\n', ''))
            else:  # if new key is to be inserted
                # using a fast hashing function to create a suitable unique file name
                file_name = str(fnv1a_32(message_args[1]))
                self.add_key_to_map(file_name, message_args[1])
                self.dump_to_file(
                    file_name, message_args[3].replace('\r\n', ''))
            return "STORED\r\n"
        except Exception as e:
            self.LOG.exception('exception while set()', e)
            self.LOG.log(10, e, sys.exc_info())
            return "NOT-STORED\r\n"

    def append_key_value(self, message_args):
        self.LOG.log(20, "client fired an append query!")
        try:
            if message_args[1] in self.key_value:  # check if key is present already
                self.append_line_to_file(
                    message_args[1], message_args[3].replace('\r\n', ''))
                if self.key_value[message_args[1]] in self.file_value:
                    self.file_value[self.key_value[message_args[1]]
                                    ] += message_args[3].replace('\r\n', '')
                else:
                    self.file_value[self.key_value[message_args[1]]
                                    ] = message_args[3].replace('\r\n', '')
            else:  # if new key is to be inserted
                # using a fast hashing function to create a suitable unique file name
                file_name = str(message_args[1])
                self.add_key_to_map(file_name, message_args[1])
                self.append_line_to_file(
                    file_name, message_args[3].replace('\r\n', ''))
                self.file_value[self.key_value[message_args[1]]
                                ] = message_args[3].replace('\r\n', '')
            return "STORED\r\n"
        except Exception as e:
            self.LOG.exception('exception while append()', e)
            self.LOG.log(10, e, sys.exc_info())
            return "NOT-STORED\r\n"

# Function to get the value for a key from persistent store
    def get_key_value(self, message_args):
        self.LOG.log(20, "client fired a get query!")
        if message_args[1] not in self.key_value:
            value = ''
        else:
            if self.key_value[message_args[1]] not in self.file_value:
                fd_obj = open(os.path.join(self.values_path,
                                           self.key_value[message_args[1]]), 'rb')
                value = pickle.load(fd_obj)
                fd_obj.close()
                self.file_value[self.key_value[message_args[1]]] = value
            else:
                value = self.file_value[self.key_value[message_args[1]]]
        resp = 'VALUE ' + \
            str(message_args[1])+' ' + str(len(value)) + \
            ' \r\n' + str(value)+' \r\n' + "END\r\n"
        return resp

    def get_lines_keys_value(self, message_args):
        if message_args[1] not in self.key_value:
            value = ''
        else:
            if self.key_value[message_args[1]] not in self.file_value:
                fd_obj = open(os.path.join(self.values_path,
                                           self.key_value[message_args[1]]), 'r')
                value = fd_obj.read()
                fd_obj.close()
                self.file_value[self.key_value[message_args[1]]] = value
            else:
                value = self.file_value[self.key_value[message_args[1]]]
        resp = 'VALUE ' + \
            str(message_args[1])+' ' + str(len(value)) + \
            ' \r\n' + str(value)+' \r\n' + "END\r\n"
        return resp

# This is the worker thread that is spawned by the server process to serve the client parallely.
    def process(self, connection_socket, addr):
        while True:
            client_message = connection_socket.recv(4096)
            if not client_message:
                self.LOG.log(
                    20, "client closed connection at ip:%s port:%s", addr[0], addr[1])
                return
            self.LOG.log(20, "client message received!")
            self.LOG.log(10, client_message[:30])
            client_msg_new_line_sep = client_message.decode().split(" \r\n")
            client_msg_args = client_msg_new_line_sep[0].split(' ')
            client_msg_args.append(client_msg_new_line_sep[1])
            try:
                result = getattr(self, self.function_to_arg_map[client_msg_args[0]])(
                    client_msg_args)
                # calls set or get based on the text parsed and a function map, No need to change implementation as more functions are added
            except KeyError as e:
                self.LOG.log(
                    40, "Bad request from the client, function does not exist")
                result = 'INVALID REQUEST\r\n'
            server_message = result.encode('ascii', 'ignore')
            # if len(server_message) > 4096:
            #     msg_warning = 'MULTIMSG ' + str(len(server_message))
            #     connection_socket.send(msg_warning.encode())
            #     itr = 0
            #     while itr < len(server_message):
            #         connection_socket.send(server_message[itr:itr+4096])
            #         itr += 4096
            # else:
            connection_socket.send(server_message)
            self.LOG.log(20, "message sent to client!")
            self.LOG.log(10, server_message[:30])

    # Sets up the server on the given port number. Pass 0 as port number for the OS to assign an available port on its own.
    def port_setup(self, port_num):
        self.LOG.log(50, "Starting key-value server")
        self.read_map_from_disc()
        try:
            os.mkdir(self.values_path)
        except (FileExistsError, FileNotFoundError):
            None
        server_port = port_num
        server_name = gethostname()
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.bind((server_name, server_port))
        self.LOG.log(20, "server connected at ip:%s port:%s",
                     str(self.server_socket.getsockname()[0]), str(self.server_socket.getsockname()[1]))
        self.server_socket.listen(1)
        self.LOG.log(20, "server is ready to receive")
        return self.server_socket.getsockname()[1]

# This starts the server loop where it will listen on the port number and initiate communications with clients.
    def server_loop(self):
        try:
            while True:
                connection_socket, addr = self.server_socket.accept()
                self.LOG.log(20, "client connected at ip:%s port:%s",
                             addr[0], addr[1])
                process_thread = threading.Thread(
                    target=self.process, args=(connection_socket, addr))
                process_thread.start()
        except (KeyboardInterrupt, SystemExit):
            self.LOG.log(50, "Keyboard interrupt, Exiting the server\n")
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)
        except Exception as e:
            self.LOG.exception(e)
            self.LOG.log(10, e, sys.exc_info())
            raise e


# driver code to run server independently on a port number from config file
