This is an overall project readme.
Please go inside each folder for assignment relevant readmes and reports!

1.Assignment 1: A persistent Key value map that handles concurrent clients over TCP.
> key_value_pair_cache

2.Assignment 2: A map reduce frame work with master co-ordinating workers running map and reduce workers over sockets with fault tolerance.
> map_reduce_master


gcloud beta compute instances create key-value-server  --zone us-central1-a --source-machine-image base-map-reduce --metadata startup-script='#! /bin/bash
git clone https://github.com/rgrishigajra/Uni-CourseWork-Cloud-Project.git
cd Uni-CourseWork-Cloud-Project
export VAR=abc  
python3 server_init.py'

gcloud compute instances delete key-value-server --zone us-central1-a --quiet