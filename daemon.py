import subprocess
import socket
import json
import os
import time

# TODO server.start(): Make sure that func ends only when minecraft server is setted up and accepts stdin.
# Check if we can start two servers, and modded server

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



    def start(self)->bytes:
        is_alive = self.server.is_alive()
        if is_alive:
            return "Server already started!".encode()
        else:
            self.server.start()
            return "Server started!".encode() 

        # return f"Server couldn't start!\nstdout: {err[0]}\nstderr: {err[1]}\nreturncode{err[2]}".encode()

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


    def update_cfg(self,daemon_alive = True):

        with open("config.json","r+") as f:
            config = json.load(f)

            if self.server.process:
                config["server_pid"] = self.server.process.pid
                if self.server.is_alive() == 1:
                    config["server_alive"] = True
                else:
                    config["server_alive"] = False

            config["daemon_pid"] = os.getpid()
            config["daemon_alive"] = daemon_alive

            f.seek(0)
            json.dump(config,f,indent=4)
            f.truncate()

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

    def split_msg(self, data):
        parts = data[0].split()
            
        command = parts[0]
        arguments = parts[1:]

        return (command, arguments)

    def handle_command(self,command,arguments,client):

        if arguments:
            client.send("WIP".encode())
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

                    self.update_cfg()


        finally:
            self.socket.close()
            os.remove(self.sock_path)
            self.update_cfg(False) 
            

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

    def read_std(self):
        out = self.process.stdout.read()
        err = self.process.stderr.read()
        returncode = self.process.returncode

        return (out,err,returncode)


    def start(self)->tuple:

        self.process = subprocess.Popen(["java",f"-Xmx{self.ram}G","-jar","server.jar","nogui"],
                        stdout = subprocess.PIPE,
                        stdin = subprocess.PIPE,
                        stderr = subprocess.PIPE,
                        text = True,
                        cwd = self.path)
        
        return self.is_alive()

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
minecraft.get_selected_server()

daemon = Daemon(minecraft)
daemon.update_cfg()


daemon.communicate()