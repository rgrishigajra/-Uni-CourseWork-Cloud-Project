# Distributed Map Reduce

# Files and ways to run
### config.ini
This file has the following options:
  Decides what port the key value server runs on
 -      KeyValueServerPort = 8000
 Decides the number of Mappers
 -      NumberOfMappers = 5
 Decides the number of Reducers
 -     NumberOfReducers = 5
 Sets the detail of logs, Put WARNING for errors and key events, DEBUG for all logs
 -     LogLevel = WARNING 
 Serialized version of mapper function, Included options: mapper/word_count_mapper_serialized, mapper/inverted_index_mapper_serialized
 -     MapperCodeSerialized = mapper/word_count_mapper_serialized
  Serialized version of reducer function, Included options: mapper/word_count_reducer_serialized, mapper/inverted_index_reducer_serialized
 -     ReducerCodeSerialized = reducer/word_count_reducer_serialized'
 Out put location
 -     OutputFile = output.txt
 If set to True, a mapper might fail with 1/(No of mappers) probabality 
 -     TestMapperFail = False
If set to True, a reducer might fail with 1/(No of reducers) probabality 
 -     TestReducerFail = False

### driver_code.py

This file has the driver code. For testing purposes this alone will suffice to check the code. Run the the file as :
```bash
 python3 driver_code.py
```
 IMPORTANT:if the script has crashed before, it might give errors on port for key value store. Change that in config.ini file
 
1. The script first runs the key value server on a particular port (as an OS process in background).
2. It then boots up master (inside master/master.py)
3. It will also carry out one accuracy report test function if it is word count or inverted index functions (from provided options)

### Folder structure
--input_files (list of text files for testing)  <br />

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
# Report:
The report is a direct section by section comparison with Googles paper for the frame work.
### Design:
![image](https://user-images.githubusercontent.com/25266353/95801102-4a545c80-0cc7-11eb-9902-110714fb61aa.png)
### Programming Model
The framework takes a list of files (mentioned in config files).The user of
the MapReduce library expresses the computation as two serialized functions: Map and Reduce.  Map takes a key value pair as ('filename','string of words'). Map is supposed to provide a list of tuples as intermediate values. This will be input for a reducer function.
Reducer function needs to take a list of tuples and give back list of tuples.
Tuples need to be of (key,value) shape where as the Google implementation for both is more general.
### Examples
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
### Execution Overview:
1)Driver Program starts key value store and Master. <br />
2)Master connects to key value store. Stores a key for each Mapper worker and Reducer Worker with Value "idle". <br />
3)Master divides the input files into N keys at the key value store(one for each Mapper). This is done in round robin fashion so each file it divided into N keys.Total keys generated:No of files*No of mappers.The *Google* paper does this by M pieces of typically 16 megabytes to 64 megabytes (MB) per piece (controllable by the user via an optional parameter). In my implementation I just do it one line at a time which might be slower. Master starts its status check loop.  <br />
4)Mapperworker fetches all mapper_statuses from key value store. It assigns itself with an id which was set as "idle" by the master. It sets the value of this key in key value store as "assigned". The *Google* paper makes master and then workers that are assigned work by the master. There are M map tasks and R reduce tasks to assign. The master picks idle workers and assigns each one a map task or a reduce task. In my implementation, this is done automatically by workers picking who they are!  <br />
5)Mapper worker fetches all the keys that are meant for this id from the key value store. It then parses the contnious file into a pair of (filename, string). <br />
6)Mapper worker loads serialized function and runs it with the input (filename, string). <br />
7)Mapper worker gets output of the user map function as a list of tuples as [(k1,v1),(k2,v3)]. It then parses each tuple key as hash(key)mod No of reducers. This gives an id for reducer and the particular key value pair is assigned to this reducer. <br />
8)Mapper worker appends (key,value) pair to hash(key)mod(N)'s input file. This is done by sending the (key,value) pair to key value store but appending to the hash(key)mod(N) reducer's input file. <br />
9)After mapper has dumped the whole list, it updated the mapper_status of its id to "finished." <br />
10)During this master was looping while asking for the status of each mapper from the key value store every fixed seconds. Master decides when its been too long for a mapper to stay at 'assigned'. If that happens, master interpretes that mapper worker died and it boots a new mapper worker while setting the status as "idle". <br />
11)Once all mappers are set to "finished", the master moves to the reducer phase.It boots up N reducer workers. <br />
12)Each reducer worker does the same as mapper worker. It gets all reducer statuses and assigns itself an id from the key value store. <br />
13)Once the reducer has an id, it fetches all the keys meant for itself from key value store(there shd be one per each mapper). <br />
14)The reducer parses this into a list of tuples as [(k1,v1),(k2,v2)]. This list is provided to the serialized user reduce function. <br />
15)The reducer provides back with a list of words. The list of tuples [(k1,v1),(k2,v2)] is sent by the reducer worker to the key value store to store as output(theres one for each reducer).  <br />
16)The master does the same polling in background for all reducers. when it feels that reducers have stayed "assigned" for too long,it sets the reducer status as idle and a new reducer worker is booted to take up this reducer id's work.  <br />
17)When master detects all reducers are "finished", it fetches individual outputs from the key value store and stores it at user input(through config file) file. The output is dumped in "key value" per line manner. Its human readable so can be opened by the user to read results from. <br />

## Fault Tolerance
I have implemented fault tolerance as follows:
You can test the fault tolerance by setting TestReducerFail,TestMapperFail values to True in config file. This will create an expection(thus stopping the worker) randomly in one of the workers with 1/n probability. This option is made to test how master deals with a worker that has stopped working.
### Worker Failure
In the *Google* paper The master pings every worker periodically. If no response
is received from a worker in a certain amount of time, the master marks the worker as failed. My implementation does not need the master to ping every mapper directly. It simply fetches the status of each mapper and reducer worker maintained in the key value store by the worker themselves. If the master detects a straggler, it resets the status as 'idle' and boots a new worker. The worker identifies itself by detecting the idle status at key value pair.Since intermediate data is stored on the key value store I can do intermediate resets for workers and not complete resets but that can be a future improvement.
If worker A was slow in its output and worker B was spawned to start its work but if A is still running, both work on the same data. In the end, whichever worker finishes its output first and dumps it and sets the status as "finished" master jsut moves ahead with final output.
### Master Failure
Just like the *Google* implementation, I assume master and the key value stores wont die. If they do, the user needs to boot the whole process from start.
## About Key value store
How each component communicates with key value server :

----master:
 - sets status as of each mapper and reducer process in key value store.
 - stores input for each mapper per file in key value store.
 - takes output for each reducer from key value store.
 - polls status of each mapper and reducer to detect a straggler and boot new workers

----mapper worker:
 - traveses status for all mappers and takes the id of one thats set "idle" in key value store.
 - gets the input for that its id (N files per mapper) in key value store.
 - stores output per reducer in key value store.
 - updates status in key value store as it progresses

----reducer worker:
 - traveses status for all reducers and takes the id of one thats set "idle" in key value store.
 - gets the input for that its id (N files per reducer, same as number of mappers) in key value store.
 - stores output in key value store.
 - updates status in key value store as it progresses

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

# Test Cases: 
Full logs attached in logs folder for these test cases!
1) 1 mapper 1 reducer 1 file inverted_index:
logs
![image](https://user-images.githubusercontent.com/25266353/95808869-6bbf4380-0cdb-11eb-9c72-46f905be6a63.png)
> output.txt
```txt
is file1:25
line file1:25
this file1:25
```

2) 1 mapper 1 reducer 1 file word_count:
logs
![image](https://user-images.githubusercontent.com/25266353/95809198-36672580-0cdc-11eb-8a63-be8586d06a71.png)
> output.txt
```txt
is 25
line 25
this 25
```


3) 3 mapper 3 reducer 3 files word_count (huge files, 45k lines total):
logs
![image](https://user-images.githubusercontent.com/25266353/95809577-1f750300-0cdd-11eb-9289-65cccfcd0a01.png)
![image](https://user-images.githubusercontent.com/25266353/95809603-2dc31f00-0cdd-11eb-95a7-6f34c785bc80.png)
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
4) 3 mapper 3 reducer 3 files inverted_index (huge files, 45k lines total):
logs
![image](https://user-images.githubusercontent.com/25266353/95810589-4f250a80-0cdf-11eb-968e-cc73af12becd.png)
![image](https://user-images.githubusercontent.com/25266353/95810635-6e239c80-0cdf-11eb-85d0-ee2434436ee7.png)


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
5) 4 mapper 5 reducer 3 files word_count (huge files, 45k lines total): 
***WITH FAILING MAPPERS AND REDUCERS,option in config file***
logs
![image](https://user-images.githubusercontent.com/25266353/95812316-1b4be400-0ce3-11eb-89e5-89778d4f756c.png)
1 mapper stopped working:
![image](https://user-images.githubusercontent.com/25266353/95812375-3f0f2a00-0ce3-11eb-9ca5-8410e5e619bd.png)
Master detects it and creates new mapper
![image](https://user-images.githubusercontent.com/25266353/95812426-5ea65280-0ce3-11eb-9b0c-d5602447ebd5.png)
Finish:
![image](https://user-images.githubusercontent.com/25266353/95812464-7978c700-0ce3-11eb-9385-38206c716be2.png)


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
6) 4 mapper 5 reducer 3 files inverted_index (huge files, 45k lines total):
***WITH FAILING MAPPERS AND REDUCERS,option in config file***
logs
![image](https://user-images.githubusercontent.com/25266353/95810927-1df90a00-0ce0-11eb-9aa2-86cb61d0acd4.png)
Two reducers failed! 
![image](https://user-images.githubusercontent.com/25266353/95811459-5a793580-0ce1-11eb-993a-6f126cd59e60.png)
master detects and spawns two reducers!
![image](https://user-images.githubusercontent.com/25266353/95811580-97452c80-0ce1-11eb-94ad-7832c8e697d4.png)
finished despite two failures(they were forced)
![image](https://user-images.githubusercontent.com/25266353/95811642-bcd23600-0ce1-11eb-93a9-d3d621893794.png)

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
# Key Challenges:
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













