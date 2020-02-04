import json
from templates import indexTemplate, pkgTemplate, moduleTemplate, toHtml
import requests 
import re
from cache import fetch

from generate import Module

def debug_module(pkg_name, module_name):
    all_pkgs = fetch("http://package.elm-lang.org/search.json")

    pkgs = sorted(all_pkgs, key=lambda a: a["name"].lower())
    all_pkgs_dict = {p["name"]:p for p in pkgs}
    pkg_data = all_pkgs_dict[pkg_name]

    jsonURL = "/".join(["http://package.elm-lang.org/packages", pkg_name, pkg_data["versions"][-1], "docs.json"])
    json_data = fetch(jsonURL)
    json_data_dict = {m["name"]:m for m in json_data}


    module = Module(json_data_dict[module_name], pkg_name)

    # print json_data_dict[module_name]

    with open("./assetts/debug.html", "w") as fo:  
        data = { "pkg_link": (pkg_name, "#"), "module_name":module.name, "markdown":toHtml(module.markdown).replace('<code>', '<code class="elm">')}
        fo.write(moduleTemplate(data))

