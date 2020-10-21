from key_value_pair_cache.server import server
import configparser
if __name__ == "__main__":
    server_instance = server()
    config = configparser.ConfigParser()
    config.read('config.ini')
    port_num = int(config['app_config']['KeyValueServerPort'])
    server_instance.port_setup(port_num)
    server_instance.delete_full_cache('')
    server_instance.server_loop()
