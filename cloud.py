import requests
from requests.adapters import HTTPAdapter, Retry
import settings
import os
import math
import concurrent.futures

# CREATE SESSION

SESSION = requests.session()

retries = Retry(5, backoff_factor=1, status_forcelist=[500,502,503,504], allowed_methods= ["GET","POST","PUT","DELETE"], connect=3, read=3)

SESSION.mount("https://",HTTPAdapter(max_retries=retries))
SESSION.mount("http://",HTTPAdapter(max_retries=retries)) 

def try_parse_worker():
    try:
        WORKER = settings.get_cfg().get("worker_url")
        return WORKER
    except:
        pass

WORKER = try_parse_worker()

def init():
    global WORKER
    # GET WORKER BASE URL

    WORKER = settings.get_cfg().get("worker_url")
    if not WORKER:
        raise Exception("FAILED TO INIT \'cloud.py\': NO WORKER URL FOUND IN CONFIG")

def check_worker_url(worker_url):
    r = SESSION.get(f"{worker_url}/status")
    if r.status_code < 400 and r.json()["status"] == "ok":
        return True
    else:
        return False

def get_file_names(prefix:str = "")-> None | list[str]:
    '''
    Return keys of objects or None if none found.
    '''
    r = SESSION.get(f"{WORKER}/files",params={"prefix":prefix})
    r.raise_for_status()

    names = [file["key"] for file in r.json()["files"]]

    if len(names) == 0:
        return None
    else:
        return names

def get_directories(prefix:str = "") -> list[str]:

    r = SESSION.get(f"{WORKER}/files",params={"prefix": prefix, "delimiter": "/"})
    r.raise_for_status()

    return r.json()["delimitedPrefixes"]

def get_file(key:str) -> None | bytes:

    r = SESSION.get(f"{WORKER}/files/{key}")
    if r.status_code == 404:
        return None
    elif r.status_code == 200:
        return r.content
    r.raise_for_status()
    return r.content

def get_custom_metadata(key:str = "") -> dict[str]:
    '''
    Returns dictionary of custom metadata, if wrong key raises exception.
    '''
    r = SESSION.get(f"{WORKER}/files/{key}/meta")
    r.raise_for_status()

    return r.json()["customMetadata"]

def list_files(prefix:str = "")-> list[dict]|list[None]:
    '''
    Returns list of objects with basic metadata, custom metadata not included.
    '''

    r = SESSION.get(f"{WORKER}/files",params={"prefix":prefix})
    r.raise_for_status()

    return r.json()["files"]

def make_file(key:str,body,if_match:str = None,if_none_match:str = None, metadata:dict[str,str] = None):
    headers={}

    if if_match is not None:
        headers["If-Match"] = if_match
    if if_none_match is not None:
        headers["If-None-Match"] = if_none_match
    if metadata is not None:
        metadict = {f"x-meta-{k}":v for k,v in metadata.items()}
        headers.update(metadict)

    r = SESSION.put(f"{WORKER}/files/{key}",headers=headers, data=body)
    r.raise_for_status()

def download_file(key:str, path):
    r = SESSION.get(f"{WORKER}/files/{key}",stream=True)
    r.raise_for_status()

    with open(path,"wb") as file:
        for chunk in r.iter_content(4*1024*1024):
            if chunk:
                file.write(chunk)

def upload_file(key:str, file_path):
    '''
    file_path: abs path
    '''

    if os.stat(file_path).st_size < 10 * 1024 * 1024:
        with open(file_path,"rb") as file:
            r = SESSION.put(f"{WORKER}/files/{key}", data=file)
    else:
        mpu_upload(key, file_path)

def mpu_upload(key:str, file_path:str):
    url = f"{WORKER}/files/{key}"
    part_size = 10*1024*1024

    def create_mpu():
        r = SESSION.post(url,params={"action":"mpu-create"})
        r.raise_for_status()
        return r.json()["uploadId"]
    
    def complete_mpu(upload_id, uploaded_parts):
        r = SESSION.post(url, params={"action":"mpu-complete","uploadId": upload_id},json={"parts":uploaded_parts})

        if r.status_code >= 400:
            response = SESSION.head(url)
            if response.status_code == 200:
                print("complete actually succeeded")
                return response

        return r

    def mpu_abort(upload_id):
        requests.delete(url,params={"action": "mpu-abort", "uploadId":upload_id })
    
    def upload_part(upload_id, file_name, index):

        with open(file_name, "rb") as file:
            file.seek(part_size*index)
            part = file.read(part_size)

        r = SESSION.put(url,params={"action":"mpu-uploadpart", "uploadId": upload_id, "partNumber":str(index+1)}, data=part)

        if r.status_code >=400:
            print(f"part {index} {r.status_code}",flush=True)
        
        r.raise_for_status()

        return r.json()

    # MPU

    upload_id = None
    try:
        upload_id = create_mpu()

        if os.stat(file_path).st_size == 0:
            raise ValueError("empty file")
        parts = math.ceil(os.stat(file_path).st_size / part_size)

        with concurrent.futures.ThreadPoolExecutor(6) as executor:

            futures = [ 
                executor.submit(upload_part, upload_id, file_path, index)
                for index in range(parts)]
            
            concurrent.futures.wait(futures)
            
            uploaded_parts = [future.result() for future in futures]


        response = complete_mpu(upload_id, uploaded_parts)

        response.raise_for_status()

    except Exception as e:
        print("Error, aborting..\n",e)
        if upload_id:
            mpu_abort(upload_id)
        else:
            raise

def delete_file(key:str):
    r = SESSION.delete(f"{WORKER}/files/{key}")
    r.raise_for_status()