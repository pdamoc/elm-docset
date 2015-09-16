import json
from templates import indexTemplate, pkgTemplate, moduleTemplate, toHtml
import requests 
import re

from generate import Module

def debug_module(pkg_name, module_name):
    all_pkgs = requests.get("http://package.elm-lang.org/all-packages").json()
    all_pkgs_dict = {p["name"]:p for p in all_pkgs}
    pkg_data = all_pkgs_dict[pkg_name]

    jsonURL = "/".join(["http://package.elm-lang.org/packages", pkg_name, pkg_data["versions"][0], "documentation.json"])
    json_data = requests.get(jsonURL).json()
    json_data_dict = {m["name"]:m for m in json_data}


    module = Module(json_data_dict[module_name], pkg_name)

    # print json_data_dict[module_name]

    with open("./assetts/debug.html", "w") as fo:  
        data = { "pkg_link": (pkg_name, "#"), "module_name":module.name, "markdown":toHtml(module.markdown)}
        fo.write(moduleTemplate(data))

