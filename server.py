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
def start(args):
    server = get_selected_server()
    path = server["path"]

    os.chdir(path)
    subprocess.Popen(["java",f"-Xmx{server["ram"]}G","-jar","server.jar","nogui"],stdout=subprocess.PIPE,text=True)

def stop(args):
    pass