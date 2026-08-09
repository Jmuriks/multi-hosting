import json
import subprocess
import os

def get_selected_server()-> dict:
    try:
        with open("config.json","r") as f:
            config = json.load(f)

        return config["servers"][config["selected_server"]]
    except:
        raise Exception("No server is selected")

def save_pid(pid):

    with open("config.json","r+") as f:
        config = json.load(f)
        config["server_pid"] = pid

        f.seek(0)
        json.dump(config,f,indent=4)
        f.truncate()

    
def start(args):
    server = get_selected_server()
    path = server["path"]

    process = subprocess.Popen(["java",f"-Xmx{server["ram"]}G","-jar","server.jar","nogui"],
                     stdout=subprocess.PIPE,
                     stdin = subprocess.PIPE,
                     text=True,
                     cwd=path)

    print(f"server process launched: {process.pid}")
    save_pid(process.pid)

def stop(args):
    pass