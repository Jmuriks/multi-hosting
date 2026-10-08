import json

def get_cfg()->dict|None:
    """
    Returns config as dictionary
    Returns None if config not found.    
    """
    try:
        with open("config.json","r") as file:
            cfg = json.load(file)
        return cfg
    except:
        print("No config found")
        return

def load_cfg(config:dict):
    '''
    Rewrite current Config file by given one.
    '''

    with open("config.json","w") as file:
        json.dump(config,file,indent=4)
