import json
import subprocess
import os
import socket
import time
import psutil
import config
import cloud
from datetime import datetime, timezone
from pathlib import Path


EXPIRED_TIME = 30

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

    cfg = config.get_cfg()
    
    if cfg["daemon_pid"] is not None and psutil.pid_exists(cfg["daemon_pid"]):
        return True
    else:
        return False

def start_daemon():
    main_path = Path(__file__).resolve().parent
    if not is_daemon_alive():
        daemon = subprocess.Popen(["python3","daemon.py"],cwd=main_path)
        time.sleep(1)

def lease_expired(lease:dict):
    now = datetime.now(timezone.utc)

    last_mod = datetime.fromisoformat(lease["LastModified"])

    time_delta = now - last_mod

    if time_delta.total_seconds() > EXPIRED_TIME:
        return True
    else:
        return False

def take_lease(lease_name:str, lease:dict = None):
    if lease is None:
        cloud.make_file("lease/"+lease_name, body= b"", if_none_match="*")
        return
    cloud.make_file(key = "lease/"+lease_name,body= b"",if_match= lease["ETag"])

def get_lease_name(server_path:str):
    lease_name = server_path.removesuffix("/").replace("/","-")
    return lease_name

def start(args):

    config.update()

    server = config.get_cfg()["servers"].get(args.server_name)
    if not server:
        print("Server not found")
        return

    lease_name = get_lease_name(server["server_path"])
    lease = config.get_cfg()["lease"].get(lease_name)
    if not lease:
        take_lease(lease_name)
        cloud.download_directory(server["server_path"],Path(config.get_cfg()["directory"]))
        # Start server via daemon | daemon needs to be updated

    if lease_expired(lease):
        take_lease(lease_name, lease)
        cloud.download_directory(server["server_path"],Path(config.get_cfg()["directory"]))
        start_daemon()
        print(communicate(f"start {args.server_name}"))
        
        # Start server via daemon | daemon needs to be updated
