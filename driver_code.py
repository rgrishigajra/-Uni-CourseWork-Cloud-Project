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


def get_server_ip():
    output = subprocess.run(
        "gcloud compute instances describe key-value-server4 --zone=us-central1-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)'", shell=True, check=True, stdout=subprocess.PIPE)
    ip = output.stdout.decode()[:-1]
    return ip


def get_master_ip():
    output = subprocess.run(
        "gcloud compute instances describe master-map-reduce --zone=us-central1-a --format='get(networkInterfaces[0].accessConfigs[0].natIP)'", shell=True, check=True, stdout=subprocess.PIPE)
    ip = output.stdout.decode()[:-1]
    return ip


def boot_master_instance(instance_name, startup_script):
    command = "gcloud compute instances create %s --zone us-central1-a --machine-type=e2-micro --image=ubuntu-1804-bionic-v20201014 --image-project=ubuntu-os-cloud --boot-disk-size=10GB --scopes=compute-rw,storage-ro --metadata-from-file startup-script=%s --metadata NumberOfMappers=%s,NumberOfReducers=%s,MapperCodeSerialized=%s,ReducerCodeSerialized=%s,TestMapperFail=%s,TestReducerFail=%s" % (
        instance_name, startup_script, config['app_config']['NumberOfMappers'], config['app_config']['NumberOfReducers'], config['app_config']['MapperCodeSerialized'], config['app_config']['ReducerCodeSerialized'], config['app_config']['TestMapperFail'], config['app_config']['TestReducerFail'])
    try:
        subprocess.run(command, shell=True, check=True)
    except Exception as e:
        print(e)
    return True


def boot_key_value_server(instance_name, startup_script):
    command = "gcloud compute instances create %s --zone us-central1-a --machine-type=e2-micro --image=ubuntu-1804-bionic-v20201014 --image-project=ubuntu-os-cloud --boot-disk-size=10GB --scopes=compute-rw,storage-ro --metadata-from-file startup-script=%s" % (
        instance_name, startup_script)
    try:
        subprocess.run(command, shell=True, check=True)
    except Exception as e:
        print(e)
    return True


if __name__ == "__main__":
    # print("\n\nDriver code for map_reduce running\n\n")
    config = configparser.ConfigParser()
    config.read('config.ini')
    try:
        subprocess.run('gcloud compute firewall-rules create free-for-all --description="Allows all ingress and Egress" --direction=INGRESS --priority=1000 --network=default --action=ALLOW --rules=all --source-ranges=0.0.0.0/0', shell=True,)
    except:
        None
    boot_key_value_server('key-value-server4', 'key_value_starter.sh')
    while True:
        time.sleep(10)
        try:
            test_client = client(str(get_server_ip()),
                                 int(config['app_config']['KeyValueServerPort']))
            break
        except Exception as e:
            print('waiting for server to boot up')
    print('\n\n\n Key Value Server Up\n\n\n')
    print('Booting master-map-reduce')
    boot_master_instance('master-map-reduce', 'master_starter.sh')
    print('\n\n please run the following to ssh into the master-map-reduce:\n',
          'gcloud compute ssh master-map-reduce --zone=us-central1-a ')
    print("you can see your gcloud VM dashbaord to see all the instances being created")
    print('you can view the output at:'+get_master_ip()+":5000 once its done")
