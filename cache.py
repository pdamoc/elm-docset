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
            cache[url] = requests.get(url).text
            
        with open("cache.json", "w") as fo:
            fo.write(json.dumps(cache))
    return cache[url]
