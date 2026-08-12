import subprocess
import socket
import json
import os

# TODO Daemon start func: need to make sure server can start when process doesnt exist and if process is dead
# TODO Server is_dead func: Its not intuitive and it should just return returncode or some shit but not errors or you know (requieres thinking)


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
        # if not self.server.process:

        if not self.server.process.poll():
            return "Server already online".encode()

        err = self.server.start()

        if err:
            return f"Server couldn't start!\nstdout: {err[0]}\nstderr: {err[1]}\nreturncode{err[2]}".encode()
        return "Server started!"
        



    def stop(self)->bytes:
        if self.server.is_dead():
            return f"Server is already dead ({self.server.process.returncode})".encode()
        returncode = self.server.stop()
        self.close_communication()
        return f"Server ended with {returncode} code".encode()



    def update_cfg(self):

        with open("config.json","r+") as f:
            config = json.load(f)

            if self.server.process:
                config["server_pid"] = self.server.process.pid
                if self.server.is_dead() is None:
                    config["server_alive"] = True
                else:
                    config["server_alive"] = False

            config["daemon_pid"] = os.getpid()
            config["daemon_alive"] = True

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
            self.update_cfg() #TODO Expand update_cfg so it will say in config if server is online or offline
            

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
        
        return self.is_dead()        

    def stop(self):

        self.process.stdin.write("stop\n")
        self.process.stdin.flush()
        try:
            return self.process.wait(10.0)
        except subprocess.TimeoutExpired:
            return self.process.returncode


    def is_dead(self): # Change it so it doenst return errors but simply check the status of process (Died, never started, alive) maybe retur return code
        if not self.process: # Change this!!
            return True
        
        if self.process.poll() is not None:
            return self.read_std()
        else:
            return None

minecraft = Server()
minecraft.get_selected_server()

daemon = Daemon(minecraft)

daemon.communicate()