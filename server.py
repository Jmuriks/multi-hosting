import json
import subprocess
import os
import socket
import time
import psutil
import shutil
import config
import cloud
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace


EXPIRED_TIME = 30
EXTEND_TIME = EXPIRED_TIME - 10  # messy

daemon = None

date_format = "%Y%m%dT%H%M%S%z"

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

    daemon = config.get_cfg().get("daemon")
    if not daemon:
        return False

    for pid in daemon.keys():
        if psutil.pid_exists(int(pid)):
            return True
        else:
            return False

def start_daemon():
    if is_daemon_alive():
        return
    
    main_path = Path(__file__).resolve().parent
    python_path = main_path/".venv/bin/python"

    
    daemon = subprocess.Popen([str(python_path),"daemon.py"],cwd=main_path,text=True)
    time.sleep(1)
    if daemon.poll() is not None:
        print(f"Daemon died ({daemon.returncode})")

def debug_daemon():
    for line in daemon.stdout:
        print("Daemon:",line,end="")

def lease_expired(lease:dict, force:bool = False):

    lease_status = lease.get("status")
    print(f"{lease_status}")

    if lease_status == "hybernation":
        print("Lease hybernated, server probably uploading to the cloud now.")
        return False
    elif lease_status == "broken":
        print(f"Lease is broken due to {lease.get("error")}")
        return False
    elif lease_status == "normal" or force:

        now = datetime.now(timezone.utc)

        last_mod = datetime.fromisoformat(lease["uploaded"])

        time_delta = now - last_mod

        if time_delta.total_seconds() > EXPIRED_TIME:
            print(f"{time_delta.total_seconds() > EXPIRED_TIME}, {time_delta.total_seconds()} > {EXPIRED_TIME}")
            return True
        else:
            return False

    else:
        raise ValueError(f"Unknown lease status {lease_status}")

def take_lease(lease_name:str, lease:dict = None):
    kwargs = {
        "key": "lease/"+lease_name,
        "body": b"",
        "metadata": {"owner": config.get_cfg()["device_id"], "status":"normal"}
    }

    if not lease:
        kwargs["if_none_match"] = "*"
    else:
        kwargs["if_match"] = lease["etag"]
    
    cloud.make_file(**kwargs)

def release_lease(lease:dict):
    cloud.delete_file(lease["key"])

def extend_lease_cycle(lease_name:str, stop_event, hybernate_lease):

    hybernation = False

    while not stop_event.is_set():
        if not hybernation and stop_event.wait(20):
            break

        if hybernate_lease.is_set():
            hybernation = True

            lease = get_lease(lease_name)
            cloud.make_file(lease["key"],b"",lease["etag"],metadata={"owner":lease["owner"], "status": "hybernation"})

            if stop_event.wait(timeout = 300):
                return
            else: 
                cloud.make_file(lease["key"],b"",lease["etag"],metadata={"owner":lease["owner"], "status": "broken", "error":"Hybernated lease reached timeout"})
                raise TimeoutError("Hybernated lease reached timeout")


        config.update()

        lease = get_lease(lease_name)

        if lease["owner"] != config.get_cfg()["device_id"] or lease_expired(lease):
            print(f"Ownership: {lease["owner"] != config.get_cfg()["device_id"]}\nLease expired {lease_expired(lease)}")
            raise Exception("You are not the owner of lease, or it expired.")
        
        if not stop_event.is_set():
            cloud.make_file(lease["key"],b"",lease["etag"],metadata={"owner":lease["owner"],"status":"normal"})

def sync_server_cycle(server_path:str, stop_event):
    while not stop_event.is_set():
        if stop_event.wait(config.get_cfg()["sync_period"]):
            break


def download_server(server_name:str):
    cfg = config.get_cfg()
    server = cfg["servers"][server_name]
    server_archive = server["archive"]
    if server_archive == "Uploading":
        raise Exception("Someone is uploading server on cloud.")

    archive_ext_path:Path = Path(cfg["directory"]) / server_archive
    archive_ext_path.parent.mkdir(parents=True,exist_ok=True)

    time_start = perf_counter()
    print("Downloading Server... ",end="",flush=True)

    cloud.download_file(server_archive, archive_ext_path)

    print(f"Done! ({round(perf_counter()-time_start, 1)} sec)")

    time_start = perf_counter()
    print("Unpacking Archive... ",end="",flush=True)
    
    shutil.unpack_archive(archive_ext_path, Path(cfg["directory"]) / server["server_path"], "zip")

    print(f"Done! ({round(perf_counter()-time_start, 1)} sec)")

    os.remove(str(archive_ext_path))

def load_server(server_path):
    '''
    server_path: Can be either path from daemon or from config
    '''
    # Load on cloud everything by server_path
    # Make sure not waste thousands of class A operations
    # And make it faster a bit.
    server_path1 = Path(server_path)
    server_name = server_path1.name

    cfg =  config.get_cfg()

    server = cfg["servers"].get(server_name)
    abs_path = Path(cfg["directory"]) / server["server_path"]

    archive_path = archive_server(abs_path)

    key = Path(archive_path).relative_to(cfg["directory"])
    key = key.parent / server_name / key.name

    cloud.make_file(server["server_path"]+'/'+"current.json",json.dumps({"archive": "Uploading"}))

    time_start = perf_counter()
    print("Uploading to the cloud... ",end="",flush=True)
    cloud.upload_file(str(key), archive_path)
    cloud.make_file(server["server_path"]+'/'+"current.json",json.dumps({"archive": str(key)}))
    print(f"Done! ({round(perf_counter()-time_start, 1)} sec)")

    os.remove(str(archive_path))
    
def archive_server(server_path:Path)->str:
    '''
    server_path: absolute server path
    '''

    time_start = perf_counter()
    print("Archiving Server... ",end="",flush=True)

    archive_path = str(server_path) + "_" + datetime.now(timezone.utc).strftime(date_format)
    shutil.make_archive(archive_path,
                        "zip",
                        server_path)

    print(f"Done! ({round(perf_counter()-time_start, 1)} sec)")

    return archive_path + ".zip"
    
def clean_old_server(server_path):
    archive_keys = cloud.get_file_names(server_path+"/")

    dates:list[datetime] = []
    
    for obj in archive_keys:
        if obj == server_path+"/"+"current.json":
            archive_keys.remove(obj)
            continue
        dates.append(datetime.strptime(obj.removesuffix(".zip").split("_")[-1], date_format))

    while len(dates) > 3:
        # FIND OLDEST DATE
        oldest_date = min(dates).strftime(date_format)
        dates.remove(min(dates))
        oldest_archive_key = None

        # GET ACCORDING FILE NAME
        for obj in archive_keys:
            if oldest_date in obj:
                oldest_archive_key = obj
                archive_keys.remove(obj)
        # DELETE
        cloud.delete_file(oldest_archive_key)        

def get_lease(lease_name:str)->dict:
    lease = config.get_cfg()["lease"].get(lease_name)
    if not lease:
        raise Exception(f"Wrong lease name ({lease_name})")

    return lease

def get_lease_name(server_path:str):
    lease_name = server_path.removesuffix("/").replace("/","-")
    return lease_name

def get_server(server_name:str)-> dict|None:
    return config.get_cfg()["servers"].get(server_name)

def am_i_host(server_name:str)->bool:
    '''
    Define if you're host of the server by the given name.
    '''
    server = get_server(server_name)
    if not server:
        print("Server with this name wasn't found.")
        return

    cfg = config.get_cfg()

    lease = cfg["lease"].get(get_lease_name(server["server_path"]))

    if not lease:
        print("Server isn't running by anyone.")
        return False

    if lease["owner"] == cfg["device_id"]:
        answ = communicate("send_server_path")
        if answ != server["server_path"]:
            print(f"You are hosting {answ} and not {server_name}")
            return False
        
        return True
    else:
        return False



def start(args):

    config.update()

    server = get_server(args.server_name)
    if not server:
        print("Server not found")
        return
    elif server.get("archive") == "Uploading":
        print("Someone is uploading server on cloud, try later.")
        return

    lease_name = get_lease_name(server["server_path"])
    lease = config.get_cfg()["lease"].get(lease_name)

    if lease:
        try:
            expired = lease_expired(lease)
        except ValueError:
            if clean_broken_lease(args):
                lease = None
            else:
                raise

    if not lease or expired:
        download_server(args.server_name)
        start_daemon()
        print(communicate(f"start {args.server_name}"))
        take_lease(lease_name, lease)
        config.update(False)
    else:
        print("Server lease is not expired!\nServer might be already running on other host.")

def stop(args):
    config.update()
    cfg = config.get_cfg()

    host = am_i_host(args.server_name)
    
    if not host:
        print("You are not hosting this server at the moment")
        return
    
    
    print(communicate("stop"))

    print(communicate("hybernate_lease"))
    load_server(cfg["servers"][args.server_name]["server_path"])
    print(communicate("stop_lease"))
    clean_old_server(cfg["servers"][args.server_name]["server_path"])
    
    lease = get_lease(get_lease_name(config.get_cfg()["servers"][args.server_name]["server_path"]))
    release_lease(lease)

def clean_broken_lease(args):
    lease = get_lease(get_lease_name(config.get_cfg()["servers"][args.server_name]["server_path"]))
    lease_status = lease.get("status")

    lease_requiered_keys = set(["key","etag","size","uploaded","owner","status"])

    missing = lease_requiered_keys - set(lease.keys())
    
    if missing:
        if "uploaded" not in missing and not lease_expired(lease, force=True):
            print("Cannot change unexpired lease")
            return
        release_lease(lease)
        print(f"Deleted broken lease. Was missing fields {missing}")
        return True


    elif lease_status == "broken":
        release_lease(lease)
        print("Deleted broken lease")
        return True

def retry_server_upload(args): # Maybe add log file and check there for exception during mpu before retrying.
    server = get_server(args.server_name)
    # lease = get_lease(get_lease_name(server["server_path"]))

    gamedir = Path(config.get_cfg()["directory"]) / server["server_path"]
    gamedir = gamedir.parent

    # if not lease["owner"] == config.get_cfg()["device_id"]:
    #     print("Youre dont own lease")
    #     return

    load_server(server["server_path"])

    # lease = get_lease(get_lease_name(config.get_cfg()["servers"][args.server_name]["server_path"]))
    # release_lease(lease)

    for file in os.listdir(gamedir):
        if str.startswith(file,str(gamedir.stem)) and str.endswith(file,".zip"):
            os.remove(gamedir / file)

def fix_current_json(args):
    server = get_server(args.server_name)
    server_path = server["server_path"]
    archive_keys = cloud.get_file_names(server_path+"/")
    
    dates:list[datetime] = []
    
    for obj in archive_keys:
        if obj == server_path+"/"+"current.json":
            archive_keys.remove(obj)
            continue
        dates.append(datetime.strptime(obj.removesuffix(".zip").split("_")[-1], date_format))

    recent_date = max(dates).strftime(date_format)

    for obj in archive_keys:
        if recent_date in obj:
            recent_archive_key = obj
            archive_keys.remove(obj)

    cloud.make_file(server["server_path"]+'/'+"current.json",json.dumps({"archive": str(recent_archive_key)}))
        

def fix_feature(args):
    if args.mode == "1":
        retry_server_upload(args)
    elif args.mode == "2":
        clean_broken_lease(args)
    elif args.mode == "3":
        fix_current_json(args)
