import json
import subprocess
import os
import socket
import time
import psutil
import config
from pathlib import Path

def communicate(message:str)->str:
    if not os.path.exists("/tmp/mine_daemon.sock"):
        return "Daemon socket doesn't exist"
    client = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    client.connect("/tmp/mine_daemon.sock")
    

    msg = (message + "\n").encode()

    client.send(msg)
    answer = client.recv(1024).decode()

    client.close()
    return answer

def is_daemon_alive():

    with open("config.json",'r') as f:
        config = json.load(f)
    
    if config["daemon_pid"] is not None and psutil.pid_exists(config["daemon_pid"]):
        return True
    else:
        return False

def send(args):
    if not os.path.exists("./config.json"):
        print("No server initialised")
        return
    if server_required():
        return
    if not is_daemon_alive() and args.command == "start":
        daemon = subprocess.Popen(["python3","daemon.py"],cwd=Path(".").resolve())
        time.sleep(1)

    answer = communicate(args.command)
    print(answer)



def start(args):

    config.update()

    games = config.get_cfg()["games"]

    found = False
    server_lease_key = ""
    for game_name, servers in games.items():
        if args.server_name in servers:
            found = True
            
            break

    if not found:
        print("Server with this name not found")
        return

    