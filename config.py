import json
import os
import cloud
from pathlib import Path

config_template = {
    "directory": [],
    "games": {},
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

def add_games(config:dict):
    games = cloud.get_directories()

    config["games"].update({game: {} for game in games if game != lease_dir_name})

def get_server_cfg(server_path:str):
    cfg = cloud.get_file(server_path+"mbcfg.json")

    if not cfg:
        return {}

    return json.load(cfg)
    
def add_servers(config:str):
    """
    Add server to unfinished config, game for the server must to be present in config already
    """
    for g in config["games"].keys():
        servers = cloud.get_directories(g)

        print(servers)

        if not servers:
            continue

        config["games"][g].update({s: get_server_cfg(s) for s in servers})

def build_from_cloud()->dict:
    """
    Adds games, servers, leases from cloud to config
    """
    config = get_cfg()
    if not config:
        config = config_template

    add_games(config)
    add_servers(config)
    add_lease(config)

    return config

def add_cwd(config):
    
    cur_dir = os.getcwd()
    if cur_dir not in config["directory"]:
        config["directory"].append(cur_dir)

def add_lease(config:dict):

    leases = cloud.get_file_metadata(lease_dir_name)
    if not leases:
        return

    for lease in leases:

        if lease["Key"] == lease_dir_name:
            continue

        lease["LastModified"] = lease["LastModified"].isoformat()
        config["lease"].update({lease.pop("Key"):lease})

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
