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
game = subparsers.add_parser("game")
game.add_argument("name",help= "name of the game")
game.set_defaults(config.game)
init = subparsers.add_parser("init")
init.add_argument("path",type= real_path,help="path to directory with server")
init.add_argument("--ram", default="4" , help="how many gb of ram allocate for server")
init.add_argument("-n","--name", help="server name") #default in config.py
init.add_argument("--dont-select", help="dont automatically select initialised server")
init.set_defaults(func = config.init)
select = subparsers.add_parser("select")
select.add_argument("name",help="Name of the server")
select.set_defaults(func = config.select)
deselect = subparsers.add_parser("deselect")
deselect.set_defaults(func = config.deselect)
server = subparsers.add_parser("server")
server.add_argument("command",help="Send command to server/daemon",choices=server_commands)
server.set_defaults(func = sr.send)


args = parser.parse_args()
# print(args)
args.func(args)