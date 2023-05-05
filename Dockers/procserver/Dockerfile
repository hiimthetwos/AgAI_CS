# FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04
FROM nvidia/cuda:12.0.1-runtime-ubuntu22.04

RUN export TZ="America/Boise"

RUN apt-get update

RUN DEBIAN_FRONTEND=noninteractive apt-get install tzdata 

RUN apt-get install -y python3 python3-pip vim python3-opencv

RUN apt-get install -y openssh-server

RUN ln -s /usr/bin/python3 /usr/bin/python

RUN mkdir /var/run/sshd

RUN echo 'root:password' | chpasswd

RUN sed -i 's/#PermitRootLogin.*/PermitRootLogin yes/g' /etc/ssh/sshd_config

RUN pip3 install --no-cache-dir torch

RUN pip3 install --no-cache-dir torchvision

RUN pip3 install ultralytics==8.0.54

RUN pip3 install shapely

RUN pip3 install inotify

RUN pip3 install opencv-python

RUN pip3 install pika

RUN pip3 install gputil

RUN pip3 install pymysql

RUN mkdir /agai
COPY ./dockerfiles /agai

RUN mkdir /mnt/data


EXPOSE 22
