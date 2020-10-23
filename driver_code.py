from key_value_pair_cache.server import server
import subprocess
from key_value_pair_cache.client import client
import key_value_pair_cache.helper_functions.log_helper as log_helper
import configparser
import concurrent.futures
from map_reduce_master.master import map_reduce
import time
from collections import defaultdict
import re
import subprocess


def test_output_word_count():
    print("Now testing for word count")
    inp = ''
    for file_no, file_loc in config['input_files'].items():
        with open(file_loc) as doc:
            inp += doc.read()
    encoded = inp.encode('utf-8', 'ignore')
    decoded = encoded.decode("utf-8", "ignore")
    words = re.findall(r'\w+', inp)
    freq_map = defaultdict(int)
    for word in words:
        if word.isdigit():
            continue
        freq_map[word.lower()] += 1
    with open(config['app_config']['OutputFile']) as op:
        output = op.read()
    output_words = output.split('\n')
    output_freq_map = defaultdict(int)
    for word in output_words:
        key_val_pair = word.split()
        if len(key_val_pair) == 2:
            output_freq_map[key_val_pair[0]] += int(key_val_pair[1])
    correct_words = 0
    wrong_words = 0
    for key in output_freq_map.keys():
        # print(output_freq_map[key],freq_map[key],key)
        if output_freq_map[key] == freq_map[key]:
            correct_words += 1
        else:
            wrong_words += 1
    print("List of unique words:"+str(len(freq_map)),
          "Map Reduce found correctly:"+str(len(output_freq_map)))
    print("Lost percentage of words:" +
          str(100-len(output_freq_map)*100/len(freq_map)))
    return True


def boot_master_instance(instance_name, startup_script):
    command = "gcloud compute instances create %s --zone us-central1-a --machine-type=e2-micro --image=ubuntu-1804-bionic-v20201014 --image-project=ubuntu-os-cloud --boot-disk-size=10GB --scopes=compute-rw,storage-ro --metadata-from-file startup-script=%s --metadata NumberOfMappers=%s,NumberOfReducers=%s,MapperCodeSerialized=%s,ReducerCodeSerialized=%s,TestMapperFail=%s,TestReducerFail=%s" % (
        instance_name, startup_script, config['app_config']['NumberOfMappers'], config['app_config']['NumberOfReducers'], config['app_config']['MapperCodeSerialized'], config['app_config']['ReducerCodeSerialized'], config['app_config']['TestMapperFail'], config['app_config']['TestReducerFail'])
    try:
        subprocess.run(command, shell=True, check=True)
    except Exception as e:
        print(e)
    return True


if __name__ == "__main__":
    # print("\n\nDriver code for map_reduce running\n\n")
    config = configparser.ConfigParser()
    config.read('config.ini')
    boot_master_instance('master-map-reduce-try', 'master_starter.sh')
    # key_value_server=server()
    # executor=concurrent.futures.ProcessPoolExecutor()
    # key_value_server.port_setup(
    #     int(config['app_config']['KeyValueServerPort']))
    # key_value_server.delete_full_cache('')
    # time.sleep(5)
    # server_process=executor.submit(key_value_server.server_loop)
    # # subprocess.run("python3 server_init.py",
    # #                shell=True, check=True)
    # # subprocess.run("python3 master_init.py",
    # #                shell=True, check=True)
    # master_map_reduce = map_reduce()
    # master_map_reduce.run_map_reduce()
    # if config['app_config']['MapperCodeSerialized'] == 'mapper/word_count_mapper_serialized' and config['app_config']['ConductTest'] == "True":
    #     test_output_word_count()
    # if config['app_config']['MapperCodeSerialized']=='inverted_index_reducer_serialized' and config['app_config']['ConductTest'] == "True":
    # test_output_inverted_index()
#     None
