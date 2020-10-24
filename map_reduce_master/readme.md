# Distributed Map Reduce

# Requirements:
Python 3
gcloud command line tool (with admin role)
I have automated everything, from generating key value server and master to running the map-reduce job(no hardcoded ips only fixing the port).
If you do not have a gcloud command line tool, create an instance on gcloud and ssh into it, this instance should have permissions in its service role.
I will leave an instance running for master and key value with its ip, you can give me your ssh public key and I can give ssh access. 
# Files and ways to run

### config.ini
This file has the following options:
  Decides what port the key value server runs on. This is not configurable
 -      KeyValueServerPort = 8090
 Decides the number of Mappers limit of (5) due to max instances per location limit by gcloud
 -      NumberOfMappers = 5
 Decides the number of Reducers limit of (5)
 -     NumberOfReducers = 5
 Sets the detail of logs, Put WARNING for errors and key events, DEBUG for all logs
 -     LogLevel = WARNING 
 Serialized version of mapper function, Included options: mapper/word_count_mapper_serialized, mapper/inverted_index_mapper_serialized
 -     MapperCodeSerialized = mapper/word_count_mapper_serialized
  Serialized version of reducer function, Included options: mapper/word_count_reducer_serialized, mapper/inverted_index_reducer_serialized
 -     ReducerCodeSerialized = reducer/word_count_reducer_serialized'
 Out put location. This option is not configurable.
 -     OutputFile = output.txt
 If set to True, a mapper might fail with 1/(No of mappers) probabality 
 -     TestMapperFail = False
If set to True, a reducer might fail with 1/(No of reducers) probabality 
 -     TestReducerFail = False

### driver_code.py

This file has the driver code. This creates a Master and key value server on your gcloud
```bash
 python3 driver_code.py
```
 IMPORTANT:
 
1. This script first runs a "key-value-server4" instance and runs the starter script key_value_starter.sh
2. Then starts a "master-map-reduce" instance and runs master_starter.sh, you can automate(no logs will be visible) master-map reduce with opening master_starter.sh and uncommenting the last line but you will have to wait for output.txt to generate.This will start the map reduce job, you will have to still ssh to look at output!
3.  ssh into this instance with 
``` bash
gcloud compute ssh master-map-reduce --zone=us-central1-a 
```
4. If you did not automate it run this to start master job. (Uni-CourseWork-Cloud-Project is in root directory)
``` bash
cd /Uni-CourseWork-Cloud-Project/
sudo python3 master_init.py 
```
5. open output.txt once the server finishes, this is the output.
6. close the ssh and run this delete all resources including master and key-value server.
``` bash
python3 finishing_code.py
```

# Report:
The report is a direct section by section comparison with Googles paper for the frame work.

### Programming Model
The master and key value server first boot up and master boots up mapper instances and deletes them once they are done. Then it boots up reducer instances and deletes reducer instances once they are done. 
The next paragraph is from previous assignment.
The framework takes a list of files (mentioned in config files).The user of
the MapReduce library expresses the computation as two serialized functions: Map and Reduce.  Map takes a key value pair as ('filename','string of words'). Map is supposed to provide a list of tuples as intermediate values. This will be input for a reducer function.
Reducer function needs to take a list of tuples and give back list of tuples.
Tuples need to be of (key,value) shape where as the Google implementation for both is more general.
# gcloud CLI tool
My wrote python functions to take in inputs and run these commands on the shell(they act as a library API)
I used the gcloud command line tool for booting up new instances, getting ip addresses of instances and deleting them. I use a base ubuntu since My code only needs python3, gcloud, git and this meant I dont have to isntall anything.
I use a starter script for each of the instances I run from a file. This is how they look like:
```bash
#! /bin/bash
git clone https://github.com/rgrishigajra/Uni-CourseWork-Cloud-Project.git
cd Uni-CourseWork-Cloud-Project
sudo python3 <__init__>.py
```
Each of them clones the repository and runs the init file for the python code that needs to run on the instance. For example, to run master, master_init.py file is run. 

Command for booting master:
``` bash
gcloud compute instances create %s --zone us-central1-a --machine-type=e2-micro --image=ubuntu-1804-bionic-v20201014 --image-project=ubuntu-os-cloud --boot-disk-size=10GB --scopes=compute-rw,storage-ro --metadata-from-file startup-script=%s --metadata NumberOfMappers=%s,NumberOfReducers=%s,MapperCodeSerialized=%s,ReducerCodeSerialized=%s,TestMapperFail=%s,TestReducerFail=%s" 
```
where %s values are loaded from app config in python driver code.
Command for booting key value server is similar in driver code:
``` bash
gcloud compute instances create %s --zone us-central1-a --machine-type=e2-micro --image=ubuntu-1804-bionic-v20201014 --image-project=ubuntu-os-cloud --boot-disk-size=10GB --scopes=compute-rw,storage-ro --metadata-from-file startup-script=%s"
```
worker nodes:(mapper and reducer) `preemptible` ubuntu images:
```python
def boot_instance(self, instance_name, startup_script):
            command = "gcloud compute instances create %s --zone us-central1-a --machine-type=e2-micro --image=ubuntu-1804-bionic-v20201014 --image-project=ubuntu-os-cloud --boot-disk-size=10GB --preemptible --scopes=compute-rw,storage-ro --metadata-from-file startup-script=%s" % (instance_name, startup_script)
            subprocess.run(command, shell=True, check=True)
```
delete instance api:
```python
def delete_instance(self, instance_name):
     command = "gcloud compute instances delete %s  --zone us-central1-a --quiet" % (instance_name)
    subprocess.run(command, shell=True, check=True)
```
deletes by name.

I use this to get any data from meta data set while creating the instance
```python
   def get_config(self, key):
        eq = urllib.request.Request(
            'http://metadata.google.internal/computeMetadata/v1/instance/attributes/'+str(key), headers={"Metadata-Flavor": "Google"})
        value = urllib.request.urlopen(eq).read().decode().split('.')[0]
        self.LOG.log(50, '%s : %s' % (key, value))
        return value
```
### Execution Overview:
1) Driver Program starts key value store instance and Master instance, the data from config file is sent to the instances through metadata. <br />

2) Master looks up the "key-value-store4" instance to fetch its IP address and connects to key value store. Stores a key for each Mapper worker and Reducer Worker with Value "idle". It also stores the whole config file on the key value store. <br />

3) Master divides the input files into N keys at the key value store(one for each Mapper). This is done in round robin fashion so each file it divided into N keys.Total keys generated:No of files*No of mappers.The *Google* paper does this by M pieces of typically 16 megabytes to 64 megabytes (MB) per piece (controllable by the user via an optional parameter). In my implementation I just do it one line at a time which might be slower. Master starts its status check loop.  <br />

4) Mapper PREEMPTIVE instances are created with a starter script which starts the mapper worker(the code is fetched from github).Mapper worker searches the instances for key value store and connects throught its IP. The mapper checks instance meta data (and name) for its id. .<br />
5) Mapper worker fetches all the keys that are meant for this id from the key value store. It then parses the continious file into a pair of (filename, string). <br />

6) Mapper worker loads serialized function and runs it with the input (filename, string). The name of serialized funciton is feched from the key-value store<br />

7) Mapper worker gets output of the user map function as a list of tuples as [(k1,v1),(k2,v3)]. It then parses each tuple key as hash(key)mod No of reducers(fetched from key value store). This gives an id for reducer and the particular key value pair is assigned to this reducer. <br />

8) Mapper worker appends (key,value) pair to hash(key)mod(N)'s input file. This is done by sending the (key,value) pair to key value store but appending to the hash(key)mod(N) reducer's input file. <br />

9) During this, a mapper worker thread keeps updating its status as "assigned" every 7 seconds.After mapper has dumped the whole list, its updated the mapper_status of its id to "finished." <br />

10) During this master was looping while asking for the status of each mapper from the key value store every 23 seconds.If the status of a mapper worker is "assigned", it will set it to "check". If the the status is idle, master assumes mapper worker is booting up. <br />

11) If the status is "check" then the mapper worker failed and mapper deletes and starts a new instance with the same name. The temporary work for only failed mapper is deleted. Once all mappers are set to "finished", the master moves to the reducer phase.It boots up N reducer PREEMPTIVE workers. <br />

12) Each reducer worker does the same as mapper worker. It gets the its id form meta data and config options form key value store. <br />

13) Once the reducer has an id, it fetches all the keys meant for itself from key value store(there shd be one chunk per each mapper). <br />

14) The reducer parses this into a list of tuples as [(k1,v1),(k2,v2)]. This list is provided to the serialized user reduce function. <br />

15) The reducer provides back with a list of words. The list of tuples [(k1,v1),(k2,v2)] is sent by the reducer worker to the key value store to store as output(theres one for each reducer).  <br />
16) The master does the same polling in background for all reducers. If the reducer fails to convert a "check" status to "assigned", master assumes its dead and launches a new instance with same id. <br />

17) When master detects all reducers are "finished", it fetches individual outputs from the key value store and stores it at user input(through config file) file. The output is dumped in "key value" per line manner. Its human readable so can be opened by the user to read results from. <br />

## Fault Tolerance
I have used preemptive machines for mapper reducers since I have implemented fault tolerance.
### Worker Failure
- In the *Google* paper The master pings every worker periodically. If no response
is received from a worker in a certain amount of time, the master marks the worker as failed. My implementation does not need the master to ping every worker directly. It simply fetches the status of each mapper and reducer worker maintained in the key value store by the worker themselves. 
- If master sees that a worker is `assigned`, master will set its status to `check`. If the status is `idle`, master assumes worker is booting up. This check happens every 23 seconds.
- Worker node has a thread that keeps setting its status to `assigned` every 7 seconds. So worker must set the value from `check` to `assigned` atleast once before master checks again(should be 3 times actually)
- If master sees the value `check`, it means the worker failed since there is no other way the worker did not update its status for 23 seconds. The instance that is marked as failed, is deleted and new instance with same name is booted up.
- The new instance worker cleans the files its going to write to(any residue from crashed worker).
- When the worker is done, it sets its value to `finished`
- The Master stops the status `check` loop when all the workers are `finished`
### Master Failure
Just like the *Google* implementation, I assume master and the key value stores wont die. If they do, the user needs to boot the whole process from start.
## About Key value store
How each component communicates with key value server :

----master:
 - sets status as of each mapper and reducer process in key value store.
 - sets Number of mappers, reducers, what mapper function and reducer funciton to use.
 - stores input for each mapper per file in key value store.
 - takes output for each reducer from key value store.
 - polls status of each mapper and reducer to detect a straggler and boot new workers

----mapper worker:
 - Fetches config data from key value store
 - gets the input for that its id (N files per mapper) in key value store.
 - stores output per reducer in key value store.
 - updates status in key value store as it progresses

----reducer worker:
 - Fetches config data from key value store
 - gets the input for that its id (N files per reducer, same as number of mappers) in key value store.
 - stores output in key value store.
 - updates status in key value store as it progresses

# Test Cases: (logs show me using preemptible vms)
Full logs attached in logs folder for these test cases!


1) 3 mapper 3 reducer 3 files word_count (huge files, 45k lines total) Takes 10 minutes:
logs

![image](https://user-images.githubusercontent.com/25266353/97066055-ead83580-157f-11eb-834f-0e448193822b.png)
![image](https://user-images.githubusercontent.com/25266353/97066067-19eea700-1580-11eb-890b-99739bdd0d7f.png)
![image](https://user-images.githubusercontent.com/25266353/97065961-30483300-157f-11eb-8b59-325744fa0c40.png)
![image](https://user-images.githubusercontent.com/25266353/97066026-b5cbe300-157f-11eb-8aa8-dd8f46063dcc.png)
cloud logs 
![image](https://user-images.githubusercontent.com/25266353/97066171-4525c600-1581-11eb-8dfb-0ab11a83cbd2.png)


output
```txt
amount 4
amputate 1
amusement 6
amusements 2
amusing 2
an 390
........
```
2) 3 mapper 3 reducer 3 files inverted_index (huge files, 45k lines total):
logs
![image](https://user-images.githubusercontent.com/25266353/97066183-566ed280-1581-11eb-9ea3-74f78d76b2d2.png)
![image](https://user-images.githubusercontent.com/25266353/97066225-aea5d480-1581-11eb-8424-12f93496473e.png)
![image](https://user-images.githubusercontent.com/25266353/97066246-e7de4480-1581-11eb-962a-d7ee743f8708.png)


output
```txt
along file1:2,file2:77,file3:2
alpha file3:1
also file1:13,file2:1,file3:116
alter file2:1,file3:2
alteration file1:3,file3:1
alternative file1:1,file3:1
........
```
3) 4 mapper 3 reducer 3 files inverted_index (huge files, 45k lines total) (20 mins due to VM forced failures): 
***killing mappers and reducer instances***
logs
![image](https://user-images.githubusercontent.com/25266353/97066472-d6963780-1583-11eb-988a-b49e64d92d4b.png)

 mapper3 stopped:
 ![image](https://user-images.githubusercontent.com/25266353/97066512-34c31a80-1584-11eb-9d8e-baad86c4726b.png)
master notices and deletes the stopped vm first if it exists and then creates a new VM
 ![image](https://user-images.githubusercontent.com/25266353/97066492-f88fba00-1583-11eb-9610-5c4935ef0641.png)
 Mapping still finishes and reducers are spawned
 ![image](https://user-images.githubusercontent.com/25266353/97066576-879cd200-1584-11eb-8016-dd17e556592c.png)

Reducer VM stopped :
![image](https://user-images.githubusercontent.com/25266353/97066709-91730500-1585-11eb-99c7-84b104b4bfa0.png)
![image](https://user-images.githubusercontent.com/25266353/97066750-eb73ca80-1585-11eb-95fe-ca54c72e1251.png)
![image](https://user-images.githubusercontent.com/25266353/97066771-08100280-1586-11eb-9320-14ad456ebb28.png)
Master notices and starts new reducer 2:
![image](https://user-images.githubusercontent.com/25266353/97066795-3261c000-1586-11eb-81b6-9e210e256baf.png)
![image](https://user-images.githubusercontent.com/25266353/97066899-971d1a80-1586-11eb-9585-69a7fff6caba.png)


output
```txt
along file1:2,file2:77,file3:2
alpha file3:1
also file1:13,file2:1,file3:116
alter file2:1,file3:2
alteration file1:3,file3:1
alternative file1:1,file3:1
........
```
4) 3 mapper 2 reducer 3 files word count (huge files, 45k lines total) (20 mins due to VM forced failures): 
***killing mappers and reducer instances***:
logs
start
![image](https://user-images.githubusercontent.com/25266353/97067125-78b81e80-1588-11eb-8889-c8e80a1b5981.png)
stopping the mapper 2 and the master does a reboot and mapper work still finsihes:
![image](https://user-images.githubusercontent.com/25266353/97067168-c6348b80-1588-11eb-903c-9cff3105ed43.png)
![image](https://user-images.githubusercontent.com/25266353/97067187-fed46500-1588-11eb-9a55-a7a6532db501.png)
rest of the logs
![image](https://user-images.githubusercontent.com/25266353/97067267-b8333a80-1589-11eb-875f-cc28e3096015.png)
![image](https://user-images.githubusercontent.com/25266353/97067313-1a8c3b00-158a-11eb-8908-b79705dc5bc6.png)


output
```txt
along file1:2,file2:77,file3:2
alpha file3:1
also file1:13,file2:1,file3:116
alter file2:1,file3:2
alteration file1:3,file3:1
alternative file1:1,file3:1
........
```
# Key Challenges and interesting test case:
## imporvements:
My design assumes that workers will only fail after they boot up and tell the master they have started, if they fail at boot up, master will just keep waiting thinking the worker is booting up. 
### The hashing: (this is from previous assignment, helped me here!)
The hashing at first might look like a needless complexity. But it simplifies the file name generating and it gives both the uniqueness a UUID name generator would provide but also a logical link that you can generate it any time you get the key. This would also generalize file name lengths to a good level.
**So, Which hashing function and why?**
The famous hashing functions SHA, MD5 are too computation heavy and more valuable cryptographically so they are booted out from the start. While researching hashing functions I came across https://softwareengineering.stackexchange.com/questions/49550/which-hashing-algorithm-is-best-for-uniqueness-and-speed/145633#145633
It is a research and comparison on between hashing functions and it puts forward  FNV-1a as superior than others:
http://www.isthe.com/chongo/tech/comp/fnv/index.html#FNV-param
Since the code for the hasher was easy and with no dependancoes I chose FNV-1a
# Assumptions:
 - The data structure is one, refer to type section for details
 - The reducer gets the whole list, not grouped by 'key' since use of combiners was not suggested. User function needs to combine per key.
 - There might be loss of data over sending it to the network if the text provided can not encoded properly. This can be seen in one of the test cases!

### Folder structure
--input_files (list of text files for testing)  <br />
--init files and bash starter files for mapper, reducer, master, key value server.
--key_value_pair_cache (has server and client implementation for key value store) <br />

--map_reduce_master <br />
    |--------master.py (master)

--mapper  <br />
    |--------mapper.py (mapper worker)  <br />
    |--------word_count_mapper.py (dumps word_count_mapper_serialized when run) <br />
    |--------word_count_mapper_serialized (serialized mapper,set in config file to use) <br />
    |--------inverted_index_mapper.py (dumps inverted_index_mapper_serialized when run) <br />
    |--------inverted_index_mapper_serialized (serialized mapper,set in config file to use) <br /> <br />

--reducer <br />
    |--------reducer.py (reducer worker) <br />
    |--------word_count_reducer.py (dumps word_count_reducerr_serialized when run) <br />
    |--------word_count_reducer_serialized (serialized reducer,set in config file to use) <br />
    |--------inverted_index_reducer.py (dumps inverted_index_reducer_serialized when run) <br />
    |--------inverted_index_reducer_serialized (serialized reducer,set in config file to use) <br />

### Examples (same as assignment 1)
Example for mapper and reducer (that are serialized and stored as word_count_mapper_serilized in mapper folder)
input ("file1","This is the string")
```python
def word_count_mapper(key, value):
    words = re.findall(r'\w+', value)
    word_dict = defaultdict(int)
    for word in words:
        if word.isdigit():
            continue
        word_dict[word.lower()] += 1
    word_list = [(key, word_dict[key]) for key in word_dict.keys()]
    return word_list
```
output ("this","1"),('is','1'),('the','1')('string','1') and input for reducer is this * number of reducers.
```python
def inverted_index_reducer(input_list):
    word_dict = defaultdict(lambda: defaultdict(int))
    for word in input_list:
        word_dict[word[0]][word[1]] += 1
    word_list = []
    for word in word_dict.keys():
        val=''
        for fil in word_dict[word].keys():
            val+=str(fil)+":"+str(word_dict[word][fil])+','
        word_list.append((word, val[:-1]))
    word_list.sort()
    return word_list
```
output ("this","10"),('is','10'),('the','10')('string','10')
## Types 
map (k1,v1) -> list[(k2,v2)]
reduce list(k1,v1) -> list(k2,v2)
The values are in strings, user can parse in other types if desired.

### server.py
The server maintains a persistent key value store on the disk. It does this by having a dictionary of keys thats stores file names. 
I added some functionalities for my key_value server from the previous assignment.
server accepts two types of requests on its port number for now as per specifications:
    (i) get <key> \r\n
    (ii) set <key> <value> \r\n
    (iii) ping 
            to check if up, for debugging and future user
    (iv) append <key> <value> \r\n 
            appends to a key, used for creating input/output files for reducers and mappers
    (v)searchid <key> \r\n
    searches the given keys for the substring <key>, used for getting list of map statuses, list of inputs based on an id, etc.
    (vi)getlines <key> \r\n
    Prev get function implemented only for single lines (assumptions form assignment 1, values being lesser than 4096 bytes.) This function sends endless chunk of data, due to the need for bigger chunks for this assignment.
### Data parititioning
 - My key value store always followed an abstraction, I would store a set of keys:file_names and file_names would have the value. I improved this by now having two dictionaries as the grade comment for assignment 1 suggested! I only read files if the value isnt in run time memory. So in my design, each key gets its own file. So I use the words keys and files interchangibly.

Getting to specifics for this assignment: 
 - Master creates M number of files, same as number of mappers. 
 - Each Mapper creates R number of files, R is number of reducers. Total: M * R
 - Each reducer creates 1 output, total: R







