# Multi-Hosting

## Share the responsibility of hosting with your friends.

Multi-Hosting is a tool that allows multiple users to take turns hosting the same game server on their own computers.

When the current host wants to stop hosting, another user can take over and continue running the server from the latest saved state. Multi-Hosting manages the server lifecycle and synchronizes server data between hosts.

The goal is simple: **share the responsibility of hosting without requiring one person to keep their computer running 24/7.**

Your friends can host the server whenever they want, using their own computers, while keeping the same shared world and its progress.

# Features

* Start/Stop Minecraft server
IDK, not so much features now tbh.
### In plans
* Support to more games like: "Vintage Story", "ArmA3" for example.
* Quality of life features: ls, status, ... and other commands and stuff
* GUI in a future when everything else would be working fine.

# Requirements 

* Linux (Windows coming soon)
* Bash, git, python (All of this comes with most distos)

# Installation

## Linux

* Execute installer.sh

### Other way

* mkdir -p ~/.local/bin
* git clone https://github.com/Jmuriks/multi-hosting.git ~/.local/opt/mb-server
* python3 -m venv ~/.local/opt/mb-server/.venv
* ~/.local/opt/mb-server/.venv/bin/python -m pip install -r ~/.local/opt/mb-server/requierements.txt
* ln -sfn ~/.local/opt/mb-server/launcher.sh ~/.local/bin/mb-server

# The Cloud

Multi-hosting using **"CloudFlare R2 Object Storage"** as the cloud storage for servers
You must have one for Multi-Hosting to work, its free until 10GB reached, but you should not trust me and go find out yourself.

Currently there is no way to setup cloud storage other than manually but i'll die trying to explain it here, so yall have to wait a little.

# First start
Make sure you have a directory for your servers locally be when you host them.

Write **"mb-server init"** in that directory.
You'll be prompted **"Past S3 API link here:"** Get the link from R2 Object Storage it will look like this (https://8173727c1540e7d331f19a527eb3db30.r2.cloudflarestorage.com)

# Usage

Currently Multi-Hosting has only three working commands:
* init
* start [Server_Name]
* stop [Server_Name]

# Limitations

* Cloud needs to be setted up manually
* Small functionality
* Only one game supported

# Other

Im super noob if you didn't notice.
