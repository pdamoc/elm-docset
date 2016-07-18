import json
import requests  
import os
from time import sleep

if os.path.exists("cache.json"):
    with open("cache.json") as fo:
        cache = json.loads(fo.read())
else:
    cache = {}

def get_with_retry(url):
    retries = 1
    success = False 
    ret = None
    while not success :
        try:
            ret = requests.get(url)
            success = True
        except: 
            if retries < 5: 
                retries +=1
                sleep(5)

    if (not (retries < 5)) and (not success):
        raise Exception("Tried 5 times, failed")

    return ret

def fetch(url, isJSON=True):
    if not url in cache:
        if isJSON:
            cache[url] = requests.get(url).json()
        else: 
            r = get_with_retry(url)
            if r.status_code != requests.codes.ok and url.endswith(".md"):
                r = get_with_retry(url.replace("README.md", "readme.md"))
                if r.status_code != requests.codes.ok:
                    cache[url] = "--"

            cache[url] = r.text
            
        with open("cache.json", "w") as fo:
            fo.write(json.dumps(cache))
    return cache[url]
