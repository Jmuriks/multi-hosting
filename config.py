import json
from pathlib import Path

def save_config(config):
    with open("config.json","w") as file:
        json.dump(config, file, indent=4)

def read_config():
    with open("config.json","r") as file:
        pass

def find_server_jar(dir_path:Path) -> Path: 
    
    for server_path in dir_path.rglob("server.jar"):
        return server_path
    
    raise Exception("Cannot find server in directory")

def default_server_name(args):
    if args.name:
        return str(args.name)
    return args.path.stem

def init(args):

    server_jar = find_server_jar(args.path)
    server_name = default_server_name(args)

    config = {
        server_name : {
            "path": str(args.path),
        "server_jar": str(server_jar),
        "ram": args.ram
        }
    }

    save_config(config)

    print(f"Server \"{server_name}\" initialised")

def select(args):
    pass
def deselect():
    pass
def status():
    pass