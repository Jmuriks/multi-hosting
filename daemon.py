import subprocess
import socket
import json
import os



class Daemon():
    def __init__(self, server):
        self.sock_path = "/tmp/mine_daemon.sock"
        self.socket = None
        self.buffer = ""
        self.commands = {
            "start":self.start,
            "stop":self.stop
        }
        self.server = server

        self.acceptig = False
        self.work = False



    def start(self)->bytes:
        if self.server.start():
            self.update_cfg()

            return "Server started!".encode() 
        else:
            raise Exception("Couldn't start the server!")

    def stop(self)->bytes:
        returncode = self.server.stop()
        self.close_communication()
        return f"Server ended with {returncode} code".encode()



    def update_cfg(self):

        with open("config.json","r+") as f:
            config = json.load(f)
            config["server_pid"] = self.server.process.pid

            f.seek(0)
            json.dump(config,f,indent=4)
            f.truncate()

    def create_socket(self):
        if os.path.exists(self.sock_path):
            os.remove(self.sock_path)

        self.socket = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.socket.bind(self.sock_path)

    def close_communication(self):
        self.acceptig = False
        self.work = False

    def communicate(self): # Maybe divide insides of this func to other subfunctions
        try:
            self.create_socket()
            self.socket.listen()

            self.accepting = True
            while self.accepting:

                client, addr = self.socket.accept()

                self.work = True
                while self.work:

                    msg = self.socket.recv(1024).decode()
                    if not msg:
                        client.close()
                        break
                    elif "\n" not in msg:
                        client.send("\\n wasnt found in the message".encode())
                        continue
                        
                    data = msg.split('\n')
                    data[0] = self.buffer + data[0]
                    self.buffer= data.pop()

                    parts = data[0].split()
                            
                    command = parts[0]
                    arguments = parts[1:]

                    if arguments:
                        client.send("WIP".encode())
                    elif command in self.commands:
                        client.send(self.commands[command]())
                    else:
                        client.send("Unknown command".encode())
        finally:
            self.socket.close()
            os.remove(self.sock_path)
            self.update_cfg() #TODO Expand update_cfg so it will say in config if server is online or offline
            os.close()

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
                        stderr = subprocess.PIPE,
                        text = True,
                        cwd = self.path)

        return True

    def stop(self):

        self.process.stdin.write("stop")
        self.process.stdin.flush()
        return self.process.wait(10.0)

minecraft = Server()
minecraft.get_selected_server()

daemon = Daemon(minecraft)

daemon.communicate()