import boto3
from pathlib import Path

BUCKET = "mb-server"

s3 = boto3.client("s3",
                  endpoint_url = "https://8173727c1540e7d441f59a527eb3db30.r2.cloudflarestorage.com",
                  region_name = "auto"
                  )

def get_file_names(prefix:str = "")-> None | list[str]:

    objects = s3.list_objects_v2(Bucket=BUCKET,Prefix=prefix)
    if "Contents" not in objects:
        return 

    names = []

    for name in objects["Contents"]:
        names.append(name["Key"])

    return names

def get_file_metadata(prefix:str = "")-> list[dict]|None:

    objects = s3.list_objects_v2(Bucket=BUCKET,Prefix=prefix)
    if "Contents" not in objects:
        return

    return objects["Contents"]

def get_directories(prefix:str = ""):
    response = s3.list_objects_v2(Bucket=BUCKET,Delimiter="/",Prefix=prefix)
    if "CommonPrefixes" not in response:
        print(f"No directories found in {prefix}")
        return
    
    return [p["Prefix"] for p in response["CommonPrefixes"]]

def get_file(key:str):
    try:
        file = s3.get_object(Bucket=BUCKET,Key=key)
        return file["Body"]
    except:
        return None

def download_directory(prefix:str,local_path: Path):
    """
    Download directory from cloud and recreate hierarchy
    prefix should look like a path ex. "Game/Server"
    local_path is a path where directory will be installed
    """
    insides = get_file_names(prefix)

    server_local_path = local_path / prefix
    server_local_path.mkdir(parents=True,exist_ok=True)
    

    for file in insides:

        local_file = server_local_path / file.removeprefix(prefix)
        local_file.parent.mkdir(parents=True,exist_ok=True)

        print(local_file)

        s3.download_file(BUCKET, file, str(local_file))
