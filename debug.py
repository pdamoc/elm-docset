import json
from templates import indexTemplate, pkgTemplate, moduleTemplate, toHtml
import requests 
import re
from cache import fetch

from generate import Module

def debug_module(pkg_name, module_name):
    all_pkgs = fetch("https://package.elm-lang.org/all-packages")
    # print(all_pkgs)
    # all_pkgs_dict = {p["name"]:p for p in all_pkgs}
    pkg_data = all_pkgs[pkg_name]
    # print(pkg_data)

    jsonURL = "/".join(["https://package.elm-lang.org/packages", pkg_name, pkg_data[-1], "docs.json"])
    json_data = fetch(jsonURL)
    json_data_dict = {m["name"]:m for m in json_data}


    module = Module(json_data_dict[module_name], pkg_name)

    # print( json_data_dict[module_name])

    with open("./assetts/debug.html", "wb") as fo:  
        data = { "pkg_link": (pkg_name, "#"), "module_name":module.name, "markdown":toHtml(module.markdown)}
        fo.write(moduleTemplate(data))

