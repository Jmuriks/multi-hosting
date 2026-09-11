import argparse
from pathlib import Path
import config
import server as sr

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

def real_path(value):
    path = Path(value).expanduser().resolve()

    if not path.exists():
        raise argparse.ArgumentTypeError(f"{value} is not a real path")
    
    return path

server_commands = ["start","stop","terminate"]
init = subparsers.add_parser("init")
init.set_defaults(func = config.init)
server = subparsers.add_parser("server")
server.add_argument("command",help="Send command to server/daemon",choices=server_commands)
server.set_defaults(func = sr.send)


args = parser.parse_args()
# print(args)
args.func(args)