import boto3
import settings
from pathlib import Path

BUCKET = "mb-server"

s3 = None

def init_s3(url_endpoint:str):
    global s3

    s3_api = url_endpoint.rstrip("/")
    
    s3 = boto3.client("s3",
                    endpoint_url = s3_api,
                    region_name = "auto"
                    )

def get_s3_api():
    try:
        return settings.get_cfg().get("s3_api")
    except Exception as e:
        print(f"Couldnt get S3 API\n{e}")
        return

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

def get_custom_metadata(key:str)->dict|None:
    response = s3.head_object(Bucket= BUCKET, Key= key)
    return response.get("Metadata")

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

def make_file(key:str,body,if_match:str = None,if_none_match:str = None, metadata:dict[str,str] = None):
    kwargs = {
        "Bucket": BUCKET,
        "Key": key,
        "Body": body
    }

    if if_match is not None:
        kwargs["IfMatch"] = if_match
    if if_none_match is not None:
        kwargs["IfNoneMatch"] = if_none_match
    if metadata is not None:
        kwargs["Metadata"] = metadata

    s3.put_object(**kwargs)

def download_directory(prefix:str,local_path: Path):
    """
    Download directory from cloud and recreate hierarchy
    prefix should look like a path ex. "Game/Server"
    local_path is a path where directory will be installed
    """
    insides = get_file_names(prefix)

    server_local_path = local_path / prefix
    server_local_path.mkdir(parents=True,exist_ok=True)
    
    counter = 0

    for file in insides:

        local_file = server_local_path / file.removeprefix(prefix)
        local_file.parent.mkdir(parents=True,exist_ok=True)

        counter += 1
        print(f"({counter}):",local_file)

        s3.download_file(BUCKET, file, str(local_file))

def download_file(key:str, path):
    s3.download_file(Bucket=BUCKET, Key=key, Filename=str(path))

def upload_directory(path:str, prefix:str = ""):
    director = Path(path)
    counter = 0
    for item in director.rglob("*"):
        if item.is_file():
            relative_path = item.relative_to(director)
            s3.upload_file(item,Bucket=BUCKET,Key=prefix+str(relative_path))
            counter += 1
            print(f"({counter}): {relative_path}")

def upload_file(key:str, file_path:str):
    s3.upload_file(Filename=file_path,Bucket=BUCKET,Key=key)

def delete_file(key:str,if_match:str = None):
    kwargs = {
        "Bucket":BUCKET,
        "Key":key
    }
    if if_match:
        kwargs["IfMatch"] = if_match
    s3.delete_object(**kwargs)

s3_api = get_s3_api()
if s3_api:
    init_s3(s3_api)