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

daemon = None

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
    if is_daemon_alive():
        return
    
    main_path = Path(__file__).resolve().parent
    
    daemon = subprocess.Popen(["python3","daemon.py"],cwd=main_path,text=True)
    time.sleep(1)
    if daemon.poll() is not None:
        print(f"Daemon died ({daemon.returncode})")

def debug_daemon():
    for line in daemon.stdout:
        print("Daemon:",line,end="")

def lease_expired(lease:dict):
    now = datetime.now(timezone.utc)

    last_mod = datetime.fromisoformat(lease["LastModified"])

    time_delta = now - last_mod

    if time_delta.total_seconds() > EXPIRED_TIME:
        return True
    else:
        return False

def take_lease(lease_name:str, lease:dict = None):
    kwargs = {
        "key": "lease/"+lease_name,
        "body": b"",
        "metadata": {"owner": config.get_cfg()["device_id"]}
    }

    if lease is None:
        kwargs["if_none_match"] = "*"
    else:
        kwargs["if_match"] = lease["ETag"]
    
    cloud.make_file(**kwargs)

def get_lease_name(server_path:str):
    lease_name = server_path.removesuffix("/").replace("/","-")
    return lease_name

def get_server(server_name:str)-> dict|None:
    return config.get_cfg()["servers"].get(server_name)

def am_i_host(server_name:str):
    server = get_server(server_name)
    if not server:
        print("Server with this name wasn't found.")
        return

    cfg = config.get_cfg()

    lease = cfg["lease"].get(get_lease_name(server["server_path"]))
    if lease["owner"] == cfg["device_id"] and not lease_expired(lease):

        answ = communicate("send_server_path")
        if answ != server["server_path"]:
            print("You are hosting other server, but you have all rights to be host of this server too. kys")
            return False
        
        return True

def start(args):

    config.update()

    server = get_server(args.server_name)
    if not server:
        print("Server not found")
        return

    lease_name = get_lease_name(server["server_path"])
    lease = config.get_cfg()["lease"].get(lease_name)

    if not lease or lease_expired(lease):
        take_lease(lease_name, lease)
        cloud.download_directory(server["server_path"],Path(config.get_cfg()["directory"]))
        start_daemon()
        print(communicate(f"start {args.server_name}"))
    else:
        print("Server lease is not expired!\nServer might be already running on other host.")

def stop(args):
    if not am_i_host(args.server_name):
        print("You cannot stop server that you're not a host of")
        return
    
    print(communicate("stop "+args.server_name))
    release_lease() #TODO

    