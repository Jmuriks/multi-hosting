import requests
from requests.adapters import HTTPAdapter, Retry
import settings

# CREATE SESSION

SESSION = requests.session()

retries = Retry(3, backoff_factor=1, status_forcelist=[500,502,503,504], allowed_methods= ["GET","POST","PUT","DELETE"])

SESSION.mount("https://",HTTPAdapter(max_retries=retries))
SESSION.mount("http://",HTTPAdapter(max_retries=retries)) 

WORKER: str

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
    Returns dictionary of metadata, if wrong key raises exception.
    '''
    r = SESSION.get(f"{WORKER}/files/{key}/meta")
    r.raise_for_status()

    return r.json()["customMetadata"]