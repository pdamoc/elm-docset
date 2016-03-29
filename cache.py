import json
import requests  
import os

if os.path.exists("cache.json"):
    with open("cache.json") as fo:
        cache = json.loads(fo.read())
else:
    cache = {}

def fetch(url, isJSON=True):
    if not url in cache:
        if isJSON:
            cache[url] = requests.get(url).json()
        else: 
            r = requests.get(url)
            if r.status_code != requests.codes.ok and url.endswith(".md"):
                r = requests.get(url.replace("README.md", "readme.md"))
                if r.status_code != requests.codes.ok:
                    cache[url] = "--"

            cache[url] = r.text
            
        with open("cache.json", "w") as fo:
            fo.write(json.dumps(cache))
    return cache[url]
