import json
import subprocess
import os
import socket
import time
from pathlib import Path

def get_selected_server()-> dict:
    try:
        with open("config.json","r") as f:
            config = json.load(f)

        return config["servers"][config["selected_server"]]
    except:
        raise Exception("No server is selected")

# def save_daemon_pid(pid):

#     with open("config.json","r+") as f:
#         config = json.load(f)
#         config["daemon_pid"] = pid

#         f.seek(0)
#         json.dump(config,f,indent=4)
#         f.truncate()

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
        return config["daemon_alive"]

def start(args):
    if is_daemon_alive() != True:
        daemon = subprocess.Popen(["python3","daemon.py"],cwd=Path(".").resolve())
    elif is_daemon_alive == None:
        print("daemon status unknown")
        return
    time.sleep(2)

    answer = communicate("start")
    print(answer)

def stop(args):

    answer = communicate("stop")
    print(answer)