from socket import *
import sys
import os
import helper_functions.log_helper
from helper_functions.hash_fnv1a import fnv1a_32
import threading
import pickle
import shutil
import json


class server:
    values_path = os.path.join(sys.path[0], "values")
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
    map_file_name = os.path.join(sys.path[0], "map_key_to_file")
    function_to_arg_map = {
        "set": "set_key_value",
        "get": "get_key_value",
    }
    LOG = helper_functions.log_helper._logger("server")
    key_value = {}

    def delete_full_cache(self):
        self.LOG.log(40, "You deleted the whole Cache!, starting fresh")
        try:
            shutil.rmtree(self.values_path)
            os.mkdir(self.values_path)
            os.remove(self.map_file_name)
        except (FileExistsError, FileNotFoundError):
            None
        return

    def add_key_to_map(self, file_name, key):
        self.key_value[key] = file_name
        fd = os.open(self.map_file_name, os.O_RDWR | os.O_EXLOCK | os.O_CREAT)
        fd_obj = os.fdopen(fd, 'wb')
        pickle.dump(self.key_value, fd_obj, protocol=pickle.HIGHEST_PROTOCOL)
        fd_obj.close()
        self.LOG.log(10, key[:10]+"... key added to map and dumped to disc!")
        return True

    def read_map_from_disc(self):
        if os.path.exists(self.map_file_name):
            with open(self.map_file_name, 'rb') as handle:
                b = pickle.load(handle)
                if isinstance(b, dict):
                    self.key_value = b.copy()
        else:
            self.key_value = {}
            open(self.map_file_name, 'x')
        self.LOG.log(10, "map was loaded from disc!")
        return True

    def dump_to_file(self, file_name, data_block):
        fd = os.open(os.path.join(self.values_path, file_name),
                     os.O_RDWR | os.O_EXLOCK | os.O_CREAT)
        fd_obj = os.fdopen(fd, 'wb')
        pickle.dump(data_block, fd_obj, protocol=2)
        fd_obj.close()
        self.LOG.log(10, file_name[:10]+"... file was dumped to disc!")
        return True

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

    def get_key_value(self, message_args):
        self.LOG.log(20, "client fired a get query!")
        if message_args[1] not in self.key_value:
            value = ''
        else:
            fd_obj = open(os.path.join(self.values_path,
                                       self.key_value[message_args[1]]), 'rb')
            value = pickle.load(fd_obj)
            fd_obj.close()
        resp = 'VALUE ' + \
            str(message_args[1])+' ' + str(len(value)) + \
            ' \r\n' + str(value)+' \r\n' + "END\r\n"
        return resp

    def process(self, connection_socket, addr):
        while True:
            client_message = connection_socket.recv(4096)
            if not client_message:
                self.LOG.log(
                    20, "client closed connection at ip:%s port:%s", addr[0], addr[1])
                return
            self.LOG.log(20, "client message received!")
            self.LOG.log(10, client_message[:30])
            client_msg_args = client_message.decode().split(" ")
            try:
                result = getattr(self, self.function_to_arg_map[client_msg_args[0]])(
                    client_msg_args)
                # calls set or get based on the text parsed and a function map, No need to change implementation as more functions are added
            except KeyError as e:
                self.LOG.log(
                    40, "Bad request from the client, function does not exist")
                result = 'INVALID REQUEST\r\n'
            server_message = result.encode()
            connection_socket.send(server_message)
            self.LOG.log(20, "message sent to client!")
            self.LOG.log(10, server_message[:30])

    def port_setup(self, port_num):
        self.LOG.debug("Starting server with log level: %s" %
                       self.LOG_LEVEL)
        self.read_map_from_disc()
        try:
            os.mkdir(self.values_path)
        except (FileExistsError, FileNotFoundError):
            None
        server_port = port_num
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.bind(("", server_port))
        self.LOG.log(20, "server connected at ip:%s port:%s",
                     str(self.server_socket.getsockname()[0]), str(self.server_socket.getsockname()[1]))
        self.server_socket.listen(1)
        self.LOG.log(20, "server is ready to receive")
        return self.server_socket.getsockname()[1]

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
if __name__ == "__main__":
    server_instance = server()
    port_num = int(os.environ.get('SERVER_PORT',0))
    server_instance.port_setup(port_num)
    server_instance.server_loop()
