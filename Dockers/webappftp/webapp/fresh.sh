#!/bin/bash

# Prompt for new hostname
read -p "Enter new hostname: " hostname

# Change hostname
sudo hostnamectl set-hostname $hostname

# Install Docker and NFS-common
sudo apt update
sudo apt install -y docker.io nfs-common docker-compose

docker run -d cloudflare/cloudflared:latest tunnel --no-autoupdate run --token eyJhIjoiNDE0ZTY4OTAzYmM0NGMyMzM0OWIwMTRjNTg5ZDUwZjciLCJ0IjoiMmMyN2Q2ODItMmM0Yy00OGVlLTlhNmEtNjZjNmYwOTg0ZmY5IiwicyI6Ik1ESTNaR0ZtWlRFdFpEaG1ZeTAwWWpZNUxUZ3pNR0l0TURjeFpERmtZak15WW1RNSJ9

# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sudo sh

sudo tailscale up

# Create directory and mount NFS share
sudo mkdir /mnt/data
sudo mount beartooth:/srv/data /mnt/data
echo "beartooth:/srv/data /mnt/data nfs defaults 0 0" | sudo tee -a /etc/fstab

# Start Docker Compose stack
sudo docker-compose up -d
