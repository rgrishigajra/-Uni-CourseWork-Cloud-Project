# Persistent Key Value store

# Files and ways to run

### driver_code.py

This file has the driver code. For testing purposes this alone will suffice to check the code. Run the the file as :
```bash
 python3 driver_code.py
```
 IMPORTANT:if the script has crashed before, it might give file loading errors ontrying to rerun. Kindly delete /values folder and map_key_to_file to solve it. The script makes those files again when they are deleted.
 
1.The script first runs the server on a particular port.
2.Then asks how many clients do you want to test the server with. The input for this can be a command line integer thats been tested on silo to support atleast 1000 concurrent clients (put 0 to skip). 
3.The script runs the number of clients given input as seperate processes.
4.Each client does a set request of a random key and random value and then gets the the value for the same key.
5.The entire process is logged to show whats happening. If the key that was set and the key that was got back from server match, client logs "successfull key value retrieval."
6.The driver code then gives an option to fire queries through command line. It gives 5 commands: 
 - help:lists what commands client and server support
 - exit: exits the server *note: the keys will be persistent on next reboot even if you exit*
 - set: you input two more strings as key and value one by one after entering 'set' . The client formats the message required by the server and sends the set request.
 - get: you input one more string after entering 'get'which will be the key client will ask the server for.
 - delete:This will delete the entire server cache! You will loose all data (keys and values) upon this.

### server.py
The server maintains a persistent key value store on the disk. It does this by having a dictionary of keys thats stores file names. These file names are derived by hashing the key! The seperation of values into seperate file per key was to enable faster file dumps and acesses. This way the map_file is only updated when a new key is added (the file name stays the same if the key's value is being updated!). Parallel clients only need exclusive access to files now if they are trying to contend for the same key. This removes the bottleneck that comes when the server maintains only one dictionary which stores the key and the value.

Has all server class and methods for a server. Can be run on its own as well .
It expects a port number as an environment variable called 'SERVER_PORT'. You can set the environment first by running (modify the varianbles as you want in this file before.)
```bash
. env.sh
```
And then running the server by with 
```bash
python3 server.py
```
IMPORTANT: You dont need to run this if you are running driver_code.py! This File should be run to test a stand alone server.
- the server responds with a 'INVALID REQUEST\r\n' if message is not as below:

server accepts two types of requests on its port number for now as per specifications:
    (i) get <key> \r\n
    (ii) set <key> <value> \r\n
    
--> Set:
 - Specifically, the set command is whitespace delimited, and consists of two lines:

       (i) set <key> <value-size-bytes> \r\n

       (ii) <value> \r\n

  - Note that this is a simpler version of the Memcached protocol, in which the set command also accepts flags and expiry time, which we will ignore for this assignment. The server should respond with either "STORED\r\n", or "NOT-STORED\r\n".



---> Get:
  - Retrieving data is simpler: get <key>\r\n

  - The server should respond with two lines: 

           (i) VALUE <key> <bytes> \r\n

           (ii) <data block>\r\n

  - After all the items have been transmitted, the server sends the string "END\r\n".

 - If there is no key the server should return a bytes of 0 and an empty data block
 
 ---> DELETE:
  - Deleting the whole cache: delete
  - This will delete the individual value files inside value folder
  - This will also delete the map_key_to_file that has key to file name mappings.

**You can even use the server as a class with following methods available to its instance:**
 ```bash
 server = server()
 ```
 **Methods:**
  ```bash
     def port_setup(self, port_num):
 ```
 Sets up the server on the given port number. Pass 0 as port number for the OS to assign an available port on its own. When finished, the method returns a port number the server is on. (this is incase you passes 0 and want to know which port was assigned!). 
   ```bash
     def server_loop(self):
```
This starts the server loop where it will listen on the port number and initiate communications with clients. For every client that connects it will start a worker thread that will server the client parallely! You just need to run this method and its will run till you provide a **keyboard interrupt using cntrl+C**. It calls on worker threads methods which further call methods to handle get, set, delete.

   ```bash
    def process(self, connection_socket, addr):
```
This is the worker thread that is spawned by the server process to serve the client parallely.It takes a socket the client and server have already established connection on(this is different from the server port number, that is just there for server and client to establish secondary ports).
This thread will work in parallel to support concurreny.It accepts messages from the client and deals with the request it gets on port defined by connection_socket.

   ```bash
    def get_key_value(self, message_args):
```
This function is called by a worker thread if the server receives a get request as mentioned that meets the formatting. The message is passed in message args as an array. This method fetches the file in which the value for the key is stored. It sends back the message as specifications say, returning an empty value if the key is not present. 
eg:"VALUE <key> <value_size> \r\n<data_block>\r\nEND\r\n"

    ```bash
    def dump_to_file(self, file_name, data_block):```
helper function to create a file named file_name and with the data_block it needs to store.
Uses pickle to dump the value in non human readable format. EAch of these files is independent to their key.

   ```bash
    def set_key_value(self, message_args):
```
This function is called by a worker thread if the server receives a set request as mentioned that meets the formatting.The message is passed in message args as an array. This method uses the key and a helper hash function (see below for more on the hashing) to generate a hash. The hash will be the file name inside which the value for the key will be stored. It uses the dump_to_file() to do this. Returns "STORED\r\n", or "NOT-STORED\r\n" as response.

   ```bash
    def read_map_from_disc(self):
```
Loads the map thats been stored before. Automatically called on boot up of the server. 
   ```bash
    def add_key_to_map(self, file_name, key):
```
Adds map[key] as file_name in the run time map. Whenever the map is updated, it is dumped to the disc using pickle. A lock is used to avoid simulataneous data dumps(otherwise the file gets corrupted).
   ```bash
    def delete_full_cache(self):
```
deletes the entire map(even the persistent version, along with individual value files)

 ### client.py
 Each server instance will be tied to a socket which it connects to with the server. To initializa an abject of client object, you need to pass the port number the server is running on.
 ```bash
 client_instance = client(server_port_number)
 ```
 the client class has three methods:
 ```bash
     def set_key(self, key, value):
```
takes a key and value as strings to send formatted message as per server specifications and sends a message to the individual port the client and server are talking on(this is different from the port number passed which is the one server just accepts connections on.)
Gets either "STORED\r\n", or "NOT-STORED\r\n" from the server and logs that output.
 ```bash
     def get(self, key):
```
takes a key as string and formats the message as server specification above and sends the message to the individual port the client and server are talking on. Logs the output of the server.
 ```bash
     def spawn_random_client(self, max_key, max_value)
```
This method is for testing purposes. The method generates a random key of random length upto max_key and random value upto random length or max_value. 
This method does a set of the random key set and does the get on the same key. It basically invokes set(key,value) and get (key). 
It then compares the response from the get(key) and logs as successful if the return value is same as that was set.
### helper functions:
hash_fnv1a.py
A simple fast hasher of noncryptoraphical type.Hashes a string into a value and returns the hash. Design choice on why this explained in problems faced.
log_helper.py
A simple logger intiator for the other scripts to use. Returns a logger object.

# Testing and performance evaluation:
**For each of the three tests, the client does a single set and a single get on the same key. It uses the spawn_random_client() method from client. Each of the keys is upto 30 bytes long and the values are upto 1000 bytes**

### for 10 clients as concurrent processes:
![image](https://user-images.githubusercontent.com/25266353/93724610-af101180-fb76-11ea-8041-fdee393edbf2.png)

### for 100 clients as concurrent processes:
![image](https://user-images.githubusercontent.com/25266353/93724620-c2bb7800-fb76-11ea-80de-83ef3343396e.png)

### for 1000 clients as concurrent processes:
![image](https://user-images.githubusercontent.com/25266353/93724628-cc44e000-fb76-11ea-8871-fcac184ceed9.png)

I noted that since i was logging extensively, there was considerable lag due to it. I suppose if i remove logging mode from debug(gives all logs) to just errors(only logs errors)
the time will be much faster.
### output for a simple set and get requests using the command line interface from driver:
set
![image](https://user-images.githubusercontent.com/25266353/93724633-debf1980-fb76-11ea-96ee-2cb4fba5a777.png)
get
![image](https://user-images.githubusercontent.com/25266353/93724653-0615e680-fb77-11ea-8a1c-79b6a69d8ca9.png)

### Testing for a key thats not there, with driver code.
![image](https://user-images.githubusercontent.com/25266353/93724657-15952f80-fb77-11ea-9623-bfe014551182.png)

### an interesting test case:
Initially I was using the os.open() function with O_EXLOCK. This keeps a lock on each seperate file allowing the server to do miltiple file dumps in parallel. The operating system handles the singaling between the processes contending for same files(This will only happen if the the key is same).The issue? silo(and many old gen systems including windows) dont support this flag! I had to switch to some other mechanism. I had two choices: Either have a global lock or individual lock for each file. Global lock would remove all advantages the server got from seperating values into seperate files. I could not figure out a way to maintain a list of active files and lock them. For now the only lock I have is on the main dictionary file that stores the key to file_name dictionary.
Whats so interesting here? As I was poking around in debugger, I realized that the only time this will create errors is when two seperate clients fire get for the same key and the same time, but even that wasnt creating proper errors. This was mostly becuase the pickle dump I did was really fast and got completed before the process switched mid way. The small chance it created errors was when pickle dump was mid way and the processes switched, the value file would go corrupt in this case. But if the pickle was not interrupted, the later call wins.













