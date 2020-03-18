#!/usr/local/bin/python
# coding=utf-8

from __future__ import print_function
import shutil, os, re 
import sqlite3

import json
from cache import fetch

from html import escape


from templates import indexTemplate, pkgTemplate, moduleTemplate, toHtml
from upgrade_json import upgrade_json
import string 


opj = os.path.join

pkgsURL = "http://package.elm-lang.org/"
rexp = re.compile("(.*)\n@docs\\s+([a-zA-Z0-9_']+(?:,\\s*[a-zA-Z0-9_']+)*)")


# cleanup and preparation
def prepare():

    global docpath, db, cur

    print("cleanig up..."), 
    
    if os.path.exists("./Elm.docset"):
        shutil.rmtree("./Elm.docset")

    resPath = "./Elm.docset/Contents/Resources/"
    

    docpath = opj(resPath, 'Documents')
    os.makedirs(docpath)
    files = [
        ("icon.png", "./Elm.docset/"),
        ("Info.plist", "./Elm.docset/Contents/"),
        ("style.css", "./Elm.docset/Contents/Resources/Documents/"),
        ("packages.css", "./Elm.docset/Contents/Resources/Documents/"),
        ("highlight.pack.js", "./Elm.docset/Contents/Resources/Documents/"),
        ]
    for (fn, dest) in files:
        shutil.copyfile("./assets/"+fn, dest+fn)
    

    db = sqlite3.connect(opj(resPath, 'docSet.dsidx'))
    cur = db.cursor()

    try: cur.execute('DROP TABLE searchIndex;')
    except: pass
    cur.execute('CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);')
    cur.execute('CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);')

    print("DONE!")

def fix_missing_parentheses(arg):
    if " " in arg:
        return "(%s)"%arg
    else: 
        return arg

class Type(object):
    def __init__(self, json, mname):
        self.name = json["name"]
        self.mname = mname
        self.qualified_name = mname + "." + json["name"]
        self.safe_name = safe_name(self.name)
        self.comment = json['comment']
        self.args = json["args"]
        self.cases = json["cases"]
     
    def get_markdown(self):
        ret = ['<div style="padding: 0px; margin: 0px; width: 980px; height: 1px; background-color: rgb(216, 221, 225);"></div>']
        
        top = '<div class="mono"><br />' 
        top += name_link(self.safe_name, "type")
        if self.args : 
            top += " "+" ".join(self.args)

        for case in self.cases:
            name, args = case
            args = [ fix_missing_parentheses(arg) for arg in args]
            line = " "+name+" "+" ".join(args)
            line = fix_type(line, self.mname)
            top += "<br />"
            if self.cases.index(case): 
                top += '&nbsp;&nbsp;&nbsp;&nbsp;<span class="grey">|</span>&nbsp;'+line
            else:
                top += '&nbsp;&nbsp;&nbsp;&nbsp;<span class="grey">=</span>&nbsp;'+line
        top += "</div>"
        ret.append(top)     
            

        ret.append(self.comment)
        return "\n\n".join(ret)

    markdown = property(get_markdown)


class Alias(object):
    def __init__(self, json, mname):
        self.name = json["name"]
        self.mname = mname
        self.qualified_name = mname + "." + json["name"]
        self.safe_name = safe_name(self.name)
        self.comment = json['comment']
        self.args = json["args"]
        self.type = json["type"]
    
    def get_markdown(self):
        ret = ['<div style="padding: 0px; margin: 0px; width: 980px; height: 1px; background-color: rgb(216, 221, 225);"></div>']
        
        top = '<div class="mono"><br />'
        
        top += name_link(self.safe_name, "alias")
        if self.args : 
            top += " "+" ".join(self.args)
        
        top += '<span class="grey"> =</span> </div> '

        ret.append(top)     

        type_parts = []

        parts = list(map(lambda p : fix_type(p, self.mname), self.type.split(",")))

        if self.type.strip().startswith("(") or self.type.strip().startswith("List ("):
            ending =  "\n    )"
        else : ending =  "\n    }"

        if len(self.type) >40:
            for part in parts:
                if parts.index(part) == 0:
                    type_parts.append("    "+part)
                elif part == parts[-1]: 
                    type_parts.append("    , "+part[:-1]+ending)
                else:
                    type_parts.append("    , "+part)
        else : type_parts = ["    "+", ".join(parts)]
        ret.append("\n".join(type_parts))
        ret.append(self.comment)
        return "\n\n".join(ret)

    markdown = property(get_markdown)


valid_chars = "_'"+string.digits+string.ascii_lowercase+string.ascii_uppercase

safe_name = lambda name: escape(name if name[0] in valid_chars else "(%s)"%name)

def name_link(name, type="value"):
    if type == "value":
        return '<strong> <a class="mono" name="%s" href="#%s">%s</a> <span class="grey"> :</span> </strong>'%(name, name, name)
    elif type == "type":
        return '<strong> <span class="green"> type </span><a class="mono" name="%s" href="#%s">%s</a></strong>'%(name, name, name)
    else:
        return '<strong> <span class="green"> type alias </span><a class="mono" name="%s" href="#%s">%s</a></strong>'%(name, name, name)

def fix_type (type_data, mname):
    def fix_bit (bit):
        subp = bit.split(".")[0]
        ret = bit.replace("%s.%s"%(subp, subp), subp)
        return ret

    fix_mname = type_data.replace(mname+".", "")
    fix_after_space = " ".join(map (fix_bit, fix_mname.split()))
    

    return "(".join(map (fix_bit, fix_after_space.split("(")))

    


class Value(object):
    def __init__(self, json, mname):
        self.name = json["name"]
        self.qualified_name = mname + "." + json["name"]
        self.safe_name = safe_name(self.name)
        self.comment = json['comment']

        
        self.type = fix_type(json["type"], mname) 

        if "precedence" in json:
            self.assocPrec = (json["associativity"], json["precedence"])
        else:
            self.assocPrec = None
    
    def get_markdown(self):
        ret = ['<div style="padding: 0px; margin: 0px; width: 980px; height: 1px; background-color: rgb(216, 221, 225);"></div>']
        
        bits =  self.type.split("->")

        link = name_link(self.safe_name)+'<span class="mono">'+'<span class="grey">-&gt;</span>'.join(bits)+"</span>"
        
        if self.assocPrec:
            link += '<span class="floatright">associativity: <strong>%s</strong> / precedence: <strong>%d</strong> </span>'%self.assocPrec

        ret.append(link)  
        ret.append(self.comment)

        return "\n\n".join(ret)

    markdown = property(get_markdown)

class Module(object):
    def __init__(self, json, package):
        self.package = package
        self.name = json["name"]
        self.safe_name = safe_name(self.name)
        self.comment = json['comment']
        
        self.aliases = {v.name:v for v in map(lambda a : Alias(a, self.name), json['aliases'])}
        self.types = {v.name:v for v in map(lambda a : Type(a, self.name), json['unions'])}
        self.values = {v.name:v for v in map(lambda a : Value(a, self.name), json['values'])}
        self.operators = {v.name:v for v in map(lambda a : Value(a, self.name), json['binops'])}
        
    def insert_in_db(self, qualified_name, name, kind):
        file_name = docname(self.package, self.name)
        sname = safe_name(name)
        name = name if name[0] in valid_chars else "(%s)"%name
        
        if not DEBUG:
            cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?,?,?)', (qualified_name, kind, file_name+"#"+sname))
        return '<a name="//apple_ref/cpp/%s/%s" class="dashAnchor"></a>'%(kind, sname)

    def expand_docs(self, content):
        ret = []
        if len(content.split("@")) == 2:
            comment, hints = content.split("@")
            items = [i.strip() for i in hints.split(",")]
        else:
            parts = content.split("@")
            comment = parts[0]
            hints = ", ".join(parts[1:])

        if comment.strip() : ret.append(comment)
        
        items = [i.splitlines()[0].strip() for i in hints.split(",") if i != ""]
        
        for item in items:
            try:
                if item.startswith("docs"): item = item.split()[1]
                if item.startswith("("): item = item[1:-1]

                if item in self.values:
                    
                    da = self.insert_in_db(self.values[item].qualified_name, self.values[item].name, "Function")
                    ret.append(da) #DashAnchor
                    ret.append(self.values[item].markdown)

                elif item in self.operators:
                    
                    da = self.insert_in_db(self.operators[item].qualified_name, self.operators[item].name, "Operator")
                    ret.append(da) #DashAnchor
                    ret.append(self.operators[item].markdown)

                elif item in self.types:
                    
                    da = self.insert_in_db(self.types[item].qualified_name, self.types[item].name, "Union")
                    ret.append(da) #DashAnchor
                    ret.append(self.types[item].markdown)
                    

                elif item in self.aliases:
                    
                    da = self.insert_in_db(self.aliases[item].qualified_name, self.aliases[item].name, "Type")
                    ret.append(da) #DashAnchor
                    ret.append(self.aliases[item].markdown)
            except: 
                pass # if the item is invalid we don't introduce it.                

        return "\n\n".join(ret)

    def get_markdown(self):
        pre = self.comment.split("# ")[0]
        body = self.comment[len(pre):]

        if "@" in pre:
            pre_ = pre.split("@")[0]
            ret = [pre_]
            ret.append(self.expand_docs(pre[len(pre_):]))

        else:
            ret = [pre]

        try:
            for part in body.split("# "):
                if part:
                    title = "# "+ part.splitlines()[0]
                    ret.append(title)       

                    content = "\n".join(part.splitlines()[1:])

                    if "@" in content:
                        ret.append(self.expand_docs(content))
                    else:
                        ret.append(content)
        except:

            print ("Error in ", self.package, self.name)
            
            import traceback
            traceback.print_exc()

        return  "\n\n".join(ret)

    markdown = property(get_markdown)

def docname(pkg, module=None):
    pkg = pkg.lower()
    module = (module if module else "index")
    return ".".join([pkg.replace("/", "."), module, "html"])

def generate_all():
    global pkgs
    print("feching all packages list ..."),
    all_pkgs = fetch(pkgsURL+"search.json")
    print("DONE!") 
    pkgs = sorted(all_pkgs, key=lambda a: a["name"].lower())
    
    # generate the index
    with open(opj(docpath, "index.html"), "wb") as fo:
        fo.write(indexTemplate({"pkgs":[(pkg["name"], docname(pkg["name"]), pkg["summary"]) for pkg in pkgs]}))

    no_pkgs = len(pkgs)
    for pkg in pkgs:
        idx = pkgs.index(pkg)+1
        pkg_name = pkg["name"]
        pkg_file = docname(pkg_name)
        try:
            pkg_version = pkg["version"]
        except KeyError:
            print ("No version found, skipping package: %s"%pkg_name)
            continue
        print ("Generating package: "+pkg_name+" [% 3d / %03d]..."%(idx, no_pkgs), end="") 
 
        json = fetch( pkgsURL+"/".join(["packages", pkg_name, pkg_version, "docs"])+".json")
        # module = Module(json)
        links = []
        for module_json in json:
              
            module = Module(module_json, pkg_name)
            module_file = docname(pkg_name, module.name) 
            links.append((module.name, module_file))
            with open(opj(docpath, module_file), "wb") as fo:  
                html = toHtml(module.markdown).replace('<code>', '<code class="elm">') # fix syntax detection
                data = { "pkg_link": (pkg_name, pkg_file), "module_name":module.name, "markdown":html}
                fo.write(moduleTemplate(data))
            cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?,?,?)', (module.name + ' (' + pkg_name + ')', 'Module', module_file))

        with open(opj(docpath, pkg_file), "wb") as fo:
            data = { "pkg_name": pkg_name, "modules":links, "version":pkg_version}
            fo.write(pkgTemplate(data))
        cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?,?,?)', (pkg_name, 'Package', pkg_file))

        print ("DONE!")

DEBUG = False 
# DEBUG = True

if __name__ == '__main__':
    print("starting ...")

    if DEBUG:
        from debug import debug_module
        debug_module("pdamoc/elm-hashids", "Hashids")
    else:
        prepare()

        generate_all()
        
        db.commit()
        db.close()

    print("Alright! Take Care Now, Bye Bye Then!")
