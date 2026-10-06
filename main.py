import argparse
from pathlib import Path
import config
import server

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

def real_path(value):
    path = Path(value).expanduser().resolve()

    if not path.exists():
        raise argparse.ArgumentTypeError(f"{value} is not a real path")
    
    return path



init = subparsers.add_parser("init")
init.set_defaults(func = config.init)
start = subparsers.add_parser("start")
start.add_argument("server_name", help="Try to start the server")
start.set_defaults(func = server.start)
stop = subparsers.add_parser("stop")
stop.add_argument("server_name")
stop.set_defaults(func = server.stop)
ls = subparsers.add_parser("ls",help="List servers")
# ls.set_defaults(func = config.list_servers)

args = parser.parse_args()
# print(args)
args.func(args)