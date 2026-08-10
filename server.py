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

def save_pid(pid):

    with open("config.json","r+") as f:
        config = json.load(f)
        config["server_pid"] = pid

        f.seek(0)
        json.dump(config,f,indent=4)
        f.truncate()

def communicate(message:str)->str:
    client = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    client.connect("/tmp/mine_daemon.sock")

    msg = (message + "\n").encode()

    client.send(msg)
    answer = client.recv(1024).decode()

    client.close()
    return answer
    
def start(args):
    subprocess.Popen(["python3","daemon.py"],cwd=Path(".").resolve())
    time.sleep(2)

    answer = communicate("start")
    print(answer)

def stop(args):

    answer = communicate("stop")
    print(answer)