from key_value_pair_cache.server import server
import key_value_pair_cache.helper_functions.log_helper as log_helper
import configparser
import concurrent.futures
from map_reduce_master.master import map_reduce
import time

if __name__ == "__main__":
    print("\n\nDriver code for map_reduce running\n\n")
    config = configparser.ConfigParser()
    config.read('config.ini')
    key_value_server = server()
    executor = concurrent.futures.ProcessPoolExecutor()
    key_value_server.port_setup(int(config['app_config']['KeyValueServerPort']))
    time.sleep(5)
    server_process = executor.submit(key_value_server.server_loop)
    master_map_reduce = map_reduce()
    master_map_reduce.run_map_reduce()
    None
