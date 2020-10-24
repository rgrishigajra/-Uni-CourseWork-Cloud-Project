#! /bin/bash
git clone https://github.com/rgrishigajra/Uni-CourseWork-Cloud-Project.git
cd Uni-CourseWork-Cloud-Project
sudo apt-get update
sudo apt-get -y install python3-pip
pip3 install flask
# you can comment the line below to read logs
sudo python3 master_init.py
