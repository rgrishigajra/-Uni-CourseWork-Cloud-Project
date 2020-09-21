from client import client
from server import server
import threading
import concurrent.futures
import random
import string
import os
import time
import sys
import timeit

function_to_arg_map = {
    "set": "set_key",
    "get": "get_key",
}

'''
spawns n clients (cli input) in parallel process pool, each does a set and a get on random key value pair of lengths 20 and 1000 respectively
'''
def n_random_request_clients(port_number, n):
    starttime = timeit.default_timer()
    for c in range(n):
        client_instance = client(port_number)
        client_pool.append(executor.submit(
            client_instance.spawn_random_client, 20, 1000))
    concurrent.futures.wait(client_pool)
    print('\n\n\n All %d Clients ran one set followed by one get sucessfully!\n\n' % (n))
    print("\nTotal time for this :", timeit.default_timer() - starttime,'\n')

'''
cli for user input on set key and calling client function
'''
def set_key(client_instance):
    print("\nEnter key to set:\n")
    key = input()
    print('\nenter value to set\n')
    value = input()
    print("\nresponse that client got\n", client_instance.set_key(key, value))
    return True

'''
cli for user input on get key and calling client function
'''
def get_key(client_instance):
    print("\nEnter key to get:\n")
    key = input()
    print("\nresponse that client got\n", client_instance.get_key(key))
    return True

'''
cli for user input on all options available. 
'''
def command_line_client(port_number, server_instance):
    current_module = sys.modules[__name__]
    client_instance = client(port_number)
    while True:
        print('\nEnter a command for client: (type `help` to see what commands are available), `exit` to leave, delete to delete persistent map\n')
        command = input()
        if command == 'delete':
            print("\n\nWARNING: This will delete the persistent map and all its contents. Press 'y' to confirm\n\n")
            conf = input()
            if conf.lower() == 'y':
                server_instance.delete_full_cache()
        elif command == 'exit':
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)
        elif command == 'help':
            print(server.function_to_arg_map.keys())
        elif command in server.function_to_arg_map:
            getattr(current_module, function_to_arg_map[command])(
                client_instance)
        else:
            print('\nCould not parse input, please try `help` or try again\n')


if __name__ == "__main__":

    # for i in range(10):
    #     client_thread = threading.Thread(
    #         target=client, args=(1027,))
    #     client_thread.start()
    server_instance = server()
    executor = concurrent.futures.ProcessPoolExecutor()
    client_pool = []
    # passing 0 as port number so the OS can assign one instead thats free.
    port_number = server_instance.port_setup(0)
    server_process = executor.submit(server_instance.server_loop)
    time.sleep(5)
    print("\nEnter how many random clients do you want to run one set and one get request for:\n")
    n = input()
    n_random_request_clients(port_number, int(n))
    command_line_client(port_number, server_instance)
