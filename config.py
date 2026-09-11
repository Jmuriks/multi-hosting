import json
import os
import cloud
from pathlib import Path

config_template = {
    "directory": [],
    "games": {}
}
server_cfg_template = {}

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

    config["games"].update({game: {} for game in games})

def add_servers(config:str):
    """
    Add server to unfinished config, game for the server must to be present in config already
    """
    for g in config["games"].keys():
        servers = cloud.get_directories(g)

        print(servers)

        if not servers:
            continue

        config["games"][g].update(dict.fromkeys(servers,server_cfg_template)) # TODO Add server config from the cloud for future |CHANGE THIS !!!!!!|

def build_from_cloud():
    """
    Adds all games and servers from cloud
    """
    config = get_cfg()
    if not config:
        config = config_template

    add_games(config)
    add_servers(config)

    load_cfg(config)

    return config

def add_cwd(config):
    
    cur_dir = os.getcwd()
    if cur_dir not in config["directory"]:
        config["directory"].append(cur_dir)
    

def init(args):

    config = build_from_cloud()

    add_cwd(config)

    print("Done!")    
