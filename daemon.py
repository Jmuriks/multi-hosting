import subprocess
import socket
import json
import os
import threading
import time
import config
from queue import Queue, Empty
from pathlib import Path

# TODO server.start(): Make sure that func ends only when minecraft server is setted up and accepts stdin.
# Check if we can start two servers, and modded server

# Start func of the server. I need to learn asyncio or threading to kill the problem with readline() so it doesnt stuck on it forever.

END = object()

class Daemon():
    def __init__(self, server):
        self.sock_path = "/tmp/mine_daemon.sock"
        self.socket = None
        self.buffer = ""
        self.commands = {
            "start":self.start,
            "stop":self.stop,
            "terminate":self.terminate
        }
        self.server = server

        self.acceptig = False
        self.work = False


    def setup_server(self, server_name):
        cfg = config.get_cfg()
        server_cfg = cfg["servers"].get(server_name)
        if not server_cfg:
            raise Exception("Server not found in the config")

        self.server.path = Path(cfg["directory"]) / server_cfg["server_path"]
        self.server.ram = server_cfg.get("ram")
        

    def start(self, server_name)->bytes:

        if self.server.is_alive():
            return "Server is alive already".encode()

        self.setup_server(server_name)
        self.server.start()

        return "Server succesfully started! (probably)".encode()

    def stop(self)->bytes:
        if not self.server.is_alive():
            return f"Server is already dead ({self.server.process.returncode})".encode()
        returncode = self.server.stop()
        if returncode is None:
            return "Couldn't end the server!".encode()
        
        return f"Server ended with {returncode} code".encode()

    def terminate(self)->bytes:
        self.server.stop()
        self.close_communication()

        return "Terminating Daemon.".encode()



    def create_socket(self):
        if os.path.exists(self.sock_path):
            os.remove(self.sock_path)

        self.socket = socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.socket.bind(self.sock_path)

    def close_communication(self):
        self.accepting = False
        self.work = False

    def msg_to_data(self,msg):
        data = msg.split('\n')
        data[0] = self.buffer + data[0]
        self.buffer= data.pop()

        return data

    def split_msg(self, data:list)->tuple[str,list]:
        parts = data[0].split()
            
        command = parts[0]
        arguments = parts[1:]

        return (command, arguments)

    def handle_command(self,command,arguments,client):

        if arguments:
            client.send(self.commands[command](*arguments))
        elif command in self.commands:
            client.send(self.commands[command]())
        else:
            client.send("Unknown command".encode())

    def communicate(self):
        try:
            self.create_socket()
            self.socket.listen()

            self.accepting = True
            while self.accepting:

                client, addr = self.socket.accept()

                self.work = True
                while self.work:

                    msg = client.recv(1024).decode()
                    if not msg:
                        client.close()
                        break
                    elif "\n" not in msg:
                        client.send("\\n wasnt found in the message".encode())
                        continue
                        
                    data = self.msg_to_data(msg)

                    command, arguments = self.split_msg(data)
                    
                    self.handle_command(command,arguments,client)

        finally:
            self.socket.close()
            os.remove(self.sock_path)
            

class Server():
    def __init__(self):
        self.process = None
        self.ram = None
        self.path = None
        self.running = False
        self.stdout_q = Queue()
        self.stdout_reader = None

    def get_selected_server(self)-> dict:
        try:
            with open("config.json","r") as f:
                config = json.load(f)

            server = config["servers"][config["selected_server"]]
            self.ram = server["ram"]
            self.path = server["path"]

        except:
            raise Exception("No server is selected")

    def read_std(self):
        out = self.process.stdout.readlines()
        err = self.process.stderr.readlines()
        returncode = self.process.returncode

        return (out,err,returncode)
    
    def read_stdout(self):
        for line in self.process.stdout:
            self.stdout_q.put(line)
        self.stdout_q.put(END)

    def receive_stdout(self,tries:int)-> list[str]:
        '''
        Capture stdout in list for amount of tries.
        try counts only when failed to recieve line, and resets after successful revieve
        '''
        tri= 0
        lines = []
        while True:
            if tri >= tries:
                break
            try:
                line = self.stdout_q.get(timeout=1)
            except Empty:
                tri += 1  
                if self.process.poll is not None:
                    print(f"Process died ({self.process.returncode})")
                    break
                continue
            
            if line == END:
                print("Process closed output")
                break

            lines.append(line)

        return lines

    def start(self)->tuple:

        self.process = subprocess.Popen(["java",f"-Xmx{self.ram}G","-jar","server.jar","nogui"],
                        stdout = subprocess.PIPE,
                        stdin = subprocess.PIPE,
                        stderr = subprocess.STDOUT,
                        text = True,
                        cwd = self.path)

        self.stdout_reader = threading.Thread(target=self.read_stdout,daemon=True)
        self.stdout_reader.start()

        lines = self.receive_stdout(5)
        for line in lines:
            if "Done" in line:
                print("Server started")
                return
        print("Last message for java\n","".join(lines))
        raise Exception("Server couldn't start")

    def stop(self):

        if not self.is_alive():
            return

        for _ in range(2):
            self.process.stdin.write("stop\n")
            self.process.stdin.flush()
            try:
                return self.process.wait(10.0)
            except subprocess.TimeoutExpired:
                continue

        print("Failed to stop the server.")
        return None
        

    def is_alive(self): 
        if not self.process: # never started
            return None
        
        if self.process.poll() is not None: # dead
            return 0
        else:
            return 1 # alive

minecraft = Server()

daemon = Daemon(minecraft)

daemon.communicate()