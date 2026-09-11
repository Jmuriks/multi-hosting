import boto3

BUCKET = "mb-server"

s3 = boto3.client("s3",
                  endpoint_url = "https://8173727c1540e7d441f59a527eb3db30.r2.cloudflarestorage.com",
                  region_name = "auto"
                  )

def get_file_names(prefix:str = ""):

    objects = s3.list_objects_v2(Bucket=BUCKET,Prefix=prefix)
    if "Contents" not in objects:
        return 

    names = []

    for name in objects["Contents"]:
        names.append(name["Key"])

    return names

def get_directories(prefix:str = ""):
    response = s3.list_objects_v2(Bucket=BUCKET,Delimiter="/",Prefix=prefix)
    if "CommonPrefixes" not in response:
        print(f"No directories found in {prefix}")
        return
    
    return [p["Prefix"] for p in response["CommonPrefixes"]]
