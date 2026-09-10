import json
import os
import cloud
from pathlib import Path


config_template = {
    "selected_server": None,
    "server_pid": None,
    "server_alive": None,
    "daemon_pid":None,
    "daemon_alive":None,
    "games": {}
}

def save_config(server_config: dict):
    config = config_template
    config["servers"] =  server_config

    try:
        with open("config.json","r") as file:
            config = json.load(file)
        
        for server in config["servers"]:
            for data in server_config:
                if server == data:
                    return
                else:
                    config["servers"].update(server_config)
    except:

        with open("config.json","w") as file:
            json.dump(config, file, indent=4)

def read_config():
    with open("config.json","r") as file:
        pass

def find_server_jar(dir_path:Path) -> Path: 
    
    server_path = dir_path / "server.jar"
    
    if server_path.exists():
        return server_path
        
    raise Exception("Cannot find server in directory")

def default_server_name(args):
    if args.name:
        return str(args.name)
    return args.path.stem

def get_servers()-> dict:
    with open("config.json") as file:
        config = json.load(file)

    return config["servers"]

def check_game_name(name:str)-> bool:
    names = cloud.get_file_names()
    if not names:
        print("Cloud is empty")
        return

    prefix = name.lower()+"/"

    for n in names:
        if n.lower().startswith(prefix):
            return True

    return False

def init(args):

    # server_jar = find_server_jar(args.path)
    server_name = default_server_name(args)

    config = {
        server_name : {
            "path": str(args.path),
        # "server_jar": str(server_jar),
        "ram": args.ram
        }
    }

    save_config(config)

    print(f"Server \"{server_name}\" initialised")

def game(args):

    if check_game_name(args.name):
        game_name = args.name

    

def select(args):
    if not os.path.exists("./config.json"):
        print("No server initialised")
        return

    servers = get_servers()

    if args.name.lower() in servers:
        with open("config.json","r+") as file:
                config = json.load(file)
                config["selected_server"] = args.name.lower()

                file.seek(0)
                json.dump(config,file,indent=4)
                file.truncate()

        print(f"Selected server \"{args.name.lower()}\"")
        return
    print(f"Server not found, here are initialised servers: {', '.join(get_servers().keys())}")
    
def deselect(args):
    if not os.path.exists("./config.json"):
        print("No server initialised")
        return

    with open("config.json","r+") as file:
        config = json.load(file)
        config["selected_server"] = None

        file.seek(0)
        json.dump(config,file,indent=4)
        file.truncate()
    print("Server deselected.")

def status(args):
    pass