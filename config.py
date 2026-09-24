import json
import os
import cloud
from pathlib import Path

config_template = {
    "daemon_pid": None,
    "directory": "",
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
    cfg = cloud.get_file(server_path+"mbcfg.json")
    default = {"server_path": server_path}
    if not cfg:
        return default

    mb_cfg = json.load(cfg)
    default.update(mb_cfg) 

    return default
    
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

            server_name = server_path.removeprefix(g).removesuffix("/")

            config["servers"].update({server_name:get_server_cfg(server_path)})

def build_from_cloud()->dict:
    """
    Adds games, servers, leases from cloud to config
    """
    config = get_cfg()
    if not config:
        config = config_template

    add_servers(config)
    add_lease(config)

    return config

def add_cwd(config):
    
    cur_dir = os.getcwd()
    if cur_dir != config["directory"]:
        config["directory"] = cur_dir

def add_lease(config:dict):

    leases = cloud.get_file_metadata(lease_dir_name)
    if not leases:
        return

    for lease in leases:

        if lease["Key"] == lease_dir_name:
            continue

        lease["LastModified"] = lease["LastModified"].isoformat()
        lease_name = lease.get("Key").removeprefix(lease_dir_name).removesuffix("/")
        config["lease"].update({lease_name:lease})

def update():
    """
    Updates config
    """

    config = get_cfg()

    if not config:
        answ = input("Make this directory for servers? y/n")
        if answ.lower() != "y":
            print("Write 'mb-server init' in the directory where you want servers to be downloaded")
            return

        init()

    config = build_from_cloud()
    load_cfg(config)


def init(args = None):

    config = build_from_cloud()
    add_cwd(config)

    load_cfg(config)

    print("Done!")   
