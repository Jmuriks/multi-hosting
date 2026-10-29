import json
import os
import socket
from pathlib import Path

MAIN_DIR = Path(__file__).resolve().parent
config_path = MAIN_DIR / "config.json"

def get_cfg()->dict|None:
    """
    Returns config as dictionary
    Returns None if config not found.    
    """
    try:
        with open(config_path,"r") as file:
            cfg = json.load(file)
        return cfg
    except:
        # print("No config found")
        return

def load_cfg(config:dict):
    '''
    Rewrite current Config file by given one.
    '''

    with open(config_path,"w") as file:
        json.dump(config,file,indent=4)

def communicate(message:str)->str:
    if not os.path.exists("/tmp/mine_daemon.sock"):
        raise Exception("Daemon socket doesn't exist")
    client = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
    client.connect("/tmp/mine_daemon.sock")
    

    msg = (message + "\n").encode()

    client.send(msg)
    answer = client.recv(1024).decode()

    client.close()
    return answer

def path_to_str_server(path:Path):
    return str(path.relative_to(path.parent.parent))