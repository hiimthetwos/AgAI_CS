#!/bin/bash

# Prompt for new hostname
read -p "Enter new hostname: " hostname

# Change hostname
sudo hostnamectl set-hostname $hostname

# Add NVIDIA container runtime key
curl -s -L https://nvidia.github.io/nvidia-container-runtime/gpgkey | sudo apt-key add -

# Get distribution
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)

# Add NVIDIA container runtime repository
curl -s -L https://nvidia.github.io/nvidia-container-runtime/$distribution/nvidia-container-runtime.list | sudo tee /etc/apt/sources.list.d/nvidia-container-runtime.list

# Update apt package list
sudo apt update

# Install Docker
sudo apt install docker.io nfs-common docker-compose -y

# Install NVIDIA container toolkit
sudo apt install nvidia-container-toolkit -y

# Install NVIDIA container runtime
sudo apt install nvidia-container-runtime -y

sudo apt install nvidia-docker2

sudo rm -f /etc/apt/sources.list.d/{graphics,nvidia,cuda,lambda}*

# Reload systemd
sudo systemctl daemon-reload

# Restart Docker
sudo systemctl restart docker

# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sudo sh

sudo tailscale up

# Create directory and mount NFS share
sudo mkdir /mnt/data
sudo mount beartooth:/srv/data /mnt/data
echo "beartooth:/srv/data /mnt/data nfs defaults 0 0" | sudo tee -a /etc/fstab

# Build Docker image
sudo docker build -t agai_server_instance .

# Run Docker container with NVIDIA runtime and port 2222 forwarded
#sudo docker run --detach --network ngrok --name agai_server_instance --runtime=nvidia --gpus all -p 2222:22 agai_server /bin/bash

# Copy files to Docker container
#sudo docker cp ./dockerfiles/. agai_server_instance:/agai

#sudo docker stop agai_server_instance

#sudo docker commit agai_server_instance agai_server:latest

#sudo docker run --detach --runtime=nvidia --gpus all -p 2222:22 agai_server_instance /agai/startserver.sh
sudo docker run --network=host -v /mnt/data:/mnt/data --runtime=nvidia --gpus all -p 2222:22 agai_server_instance /agai/startserver.sh


# Get IP address of Docker container
#ip_address=$(sudo docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' agai_server_instance_run)

# Run ngrok container to expose port 22
#sudo docker run --rm --detach -e NGROK_AUTHTOKEN=2Nk59LiZwGtlaaemRamYscoHEEj_62UctWfdNxMWAuUr48E6H --network ngrok --name ngrok ngrok/ngrok:alpine tcp $ip_address:22


# Copy SSH files and set up SSH connection
#cp -R ./ssh/* ~/.ssh/
#ssh-copy-id -i ~/.ssh/id_rsa.pub root@$ip_address -p 22



