import subprocess
import socket
import json
import os

class Daemon():
    def __init__(self):
        self.sock_path = "/tmp/mine_daemon.sock"
        self.socket = None

    def update_cfg(serv_process):

        with open("config.json","r+") as f:
            config = json.load(f)
            config["server_pid"] = serv_process.pid

            f.seek(0)
            json.dump(config,f,indent=4)
            f.truncate()

    def create_socket(self):
        if os.path.exists(self.sock_path):
            os.remove(self.sock_path)

        self.socket = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.socket.bind(self.sock_path)

    def main_loop(self):
        self.create_socket()

        try:
            self.socket.listen()

            accepting = True
            while accepting:

                client, addr = self.socket.accept()

                work = True
                while work:

                    msg = self.socket.recv(1024)
                    if not msg:
                        client.close()
                        break

        finally:
            self.socket.close()
            os.remove(self.sock_path)




daemon = Daemon()

class Server():
    def __init__(self):
        self.process = None
        self.ram = None
        self.path = None
        self.running = False

    def get_selected_server(self)-> dict:
        try:
            with open("config.json","r") as f:
                config = json.load(f)

            server = config["servers"][config["selected_server"]]
            self.ram = server["ram"]
            self.path = server["path"]

        except:
            raise Exception("No server is selected")
        
    def start(self):

        self.process = subprocess.Popen(["Java",f"-Xmx{self.ram}","-jar","server.jar","nogui"],
                        stdout = subprocess.PIPE,
                        stdin = subprocess.PIPE,
                        text = True,
                        cwd = self.path)

        daemon.update_cfg(self.process.pid)

minecraft = Server()

