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



init = subparsers.add_parser("init",help="Initialise connection with cloud, and select local directory for servers")
init.set_defaults(func = config.init)
start = subparsers.add_parser("start",help="Start the server")
start.add_argument("server_name")
start.set_defaults(func = server.start)
stop = subparsers.add_parser("stop",help = "Stop the server")
stop.add_argument("server_name")
stop.set_defaults(func = server.stop)
fix = subparsers.add_parser("fix",help="Fix the server (Use only if you know what are you doing)")
fix.add_argument("server_name")
fix.add_argument("mode",choices=["1","2","3"],help="1: retry upload to the cloud\n2: delete broken lease for server\n3: fix current.json file")
fix.set_defaults(func = server.fix_feature)
ls = subparsers.add_parser("ls",help="List servers")
# ls.set_defaults(func = config.list_servers)

args = parser.parse_args()
# print(args)
args.func(args)