import json
import os
import cloud
import settings
import psutil
from pathlib import Path
from uuid import uuid4

config_template = {
    "s3_api": "",
    "device_id": None,
    "daemon": {},
    "directory": "",
    "sync_period": 3600,
    "servers": {},
    "lease": {}
}
server_cfg_template = {}

lease_dir_name = "lease/"

def update_cfg_field(field:str, value):
    '''
    Updates one field of config,
    IF no config found, makes new one
    '''
    config = config_template
    config[field] = value

    try:
        with open("config.json","r+") as file:
            cfg_file = json.load(file)

        if field not in cfg_file:
            raise Exception("Wrong field")

        cfg_file.update(field=value)
        with open("config.json","w") as file:
            json.dump(cfg_file,file,indent=4)
    except:
        print("Creating new config")
        with open("config.json","w") as file:
            json.dump(config,file,indent=4)

def get_cfg()->dict|None:
    """
    Returns config as dictionary
    Returns None if config not found.    
    """
    try:
        with open("config.json","r") as file:
            cfg = json.load(file)
        return cfg
    except:
        print("No config found")
        return

def load_cfg(config:dict):
    '''
    Rewrite current Config file by given one.
    '''

    with open("config.json","w") as file:
        json.dump(config,file,indent=4)

def get_server_cfg(server_path:str):
    cfg = cloud.get_file(server_path+"/"+"mbcfg.json")
    default = {"server_path": server_path}
    if not cfg:
        return default

    mb_cfg = json.load(cfg)
    default.update(mb_cfg)

    return default

def create_server_cfg(server_path:str) -> dict:
    '''
    Returns dict with server config
    '''
    server_path = server_path.removesuffix("/")

    cfg = {"server_path": server_path}
    mbcfg = cloud.get_file(server_path+'/'+"mbcfg.json")
    if mbcfg:
        mbcfg = json.load(mbcfg)
        cfg.update(mbcfg)

    current_archive = cloud.get_file(server_path+'/'+"current.json")
    if not current_archive:
        raise Exception("File current.json wasnt found in server directory")
    current_archive = json.load(current_archive)
    cfg.update(current_archive)

    return cfg


def add_servers(config:dict):
    """
    Add server to unfinished config
    """
    games = cloud.get_directories()
    for g in games:
        if g == lease_dir_name:
            continue

        servers = cloud.get_directories(g)
        if not servers:
            continue

        for server_path in servers:

            server_path = server_path.removesuffix("/")
            server_name = server_path.removeprefix(g)

            config["servers"].update({server_name:create_server_cfg(server_path)})

def build_from_cloud(config):
    """
    Adds games, servers, leases from cloud to config
    """

    add_servers(config)
    update_lease(config)

def add_cwd(config):
    
    cur_dir = os.getcwd()
    if cur_dir != config["directory"]:
        config["directory"] = cur_dir

def get_lease_owner(lease_key:str):
    return cloud.get_custom_metadata(lease_key).get("owner")

def update_lease(config:dict):

    config["lease"] = {}

    leases = cloud.get_file_metadata(lease_dir_name)
    if not leases:
        return

    for lease in leases:

        if lease["Key"] == lease_dir_name:
            continue

        lease["LastModified"] = lease["LastModified"].isoformat()
        lease["owner"] = get_lease_owner(lease["Key"])
        lease_name = lease.get("Key").removeprefix(lease_dir_name).removesuffix("/")

        config["lease"].update({lease_name:lease})

def add_device_id(config:dict):
    device_id = str(uuid4())
    config["device_id"] = device_id

def add_daemon(config:dict):

    try:
        respond = settings.communicate("about_me")
    except:
        return

    pid, server_path = respond.split("_",1)
    pid = str(pid)
    server_path = settings.path_to_str_server(Path(server_path))

    config["daemon"].update({pid:server_path})

def clear_daemon(config:dict):

    for pid in list(config["daemon"].keys()):
        if not psutil.pid_exists(int(pid)):
            config["daemon"].pop(pid)

def update(suggest_init:bool = True):
    """
    Updates config
    """

    config = get_cfg()

    if not config and suggest_init:
        answ = input("Make this directory for servers? y/n ")
        if answ.lower() != "y":
            raise Exception("Write 'mb-server init' in the directory where you want servers to be downloaded")
        
        init()
        return
    elif config:
        clear_daemon(config)
        add_daemon(config)
        build_from_cloud(config)
        print(config["daemon"],len(config["daemon"]))
        load_cfg(config)
    else:
        raise Exception("No config found, and doesnt suggest init.")


def init(args = None):

    s3_api = input("Past S3 API link here: ")

    config = config_template
    config["s3_api"] = s3_api

    load_cfg(config)
    cloud.init_s3(s3_api)
    

    add_cwd(config)
    add_device_id(config)
    build_from_cloud(config)

    load_cfg(config)

    print("Initialisation Done!")   
