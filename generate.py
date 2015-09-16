#!/usr/local/bin/python

import shutil, os, re 
import sqlite3

import json
from cache import fetch

from cgi import escape


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
        ("github.css", "./Elm.docset/Contents/Resources/Documents/"),
        ("highlight.pack.js", "./Elm.docset/Contents/Resources/Documents/"),
        ]
    for (fn, dest) in files:
        shutil.copyfile("./assetts/"+fn, dest+fn)
    

    db = sqlite3.connect(opj(resPath, 'docSet.dsidx'))
    cur = db.cursor()

    try: cur.execute('DROP TABLE searchIndex;')
    except: pass
    cur.execute('CREATE TABLE searchIndex(id INTEGER PRIMARY KEY, name TEXT, type TEXT, path TEXT);')
    cur.execute('CREATE UNIQUE INDEX anchor ON searchIndex (name, type, path);')

    print("DONE!")

class Type(object):
    def __init__(self, json):
        self.name = json["name"]
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
            line = " "+name+" "+" ".join(args)
            top += "<br />"
            if self.cases.index(case): 
                top += '&nbsp;&nbsp;&nbsp;&nbsp;<span class="green">|</span>'+line
            else:
                top += '&nbsp;&nbsp;&nbsp;&nbsp;<span class="green">=</span>'+line
        top += "</div>"
        ret.append(top)     
            

        ret.append(self.comment)
        return "\n\n".join(ret)

    markdown = property(get_markdown)


class Alias(object):
    def __init__(self, json):
        self.name = json["name"]
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
        
        top += '<span class="green"> =</span> </div> '

        ret.append(top)     

        type_parts = []
        parts = self.type.split(",")
        for part in parts:
            if parts.index(part) == 0:
                type_parts.append("    "+part)
            elif part == parts[-1]:
                type_parts.append("    "+part[:-1]+"\n    }")
            else:
                type_parts.append("    , "+part)
        ret.append("\n".join(type_parts))
        ret.append(self.comment)
        return "\n\n".join(ret)

    markdown = property(get_markdown)


valid_chars = "_'"+string.digits+string.lowercase+string.uppercase

safe_name = lambda name: escape(name if name[0] in valid_chars else "(%s)"%name)

def name_link(name, type="value"):
    if type == "value":
        return '<strong> <a class="mono" name="%s" href="#%s">%s</a> <span class="green"> :</span> </strong>'%(name, name, name)
    elif type == "type":
        return '<strong> <span class="green"> type </span><a class="mono" name="%s" href="#%s">%s</a></strong>'%(name, name, name)
    else:
        return '<strong> <span class="green"> type alias </span><a class="mono" name="%s" href="#%s">%s</a></strong>'%(name, name, name)
        
class Value(object):
    def __init__(self, json):
        self.name = json["name"]
        self.safe_name = safe_name(self.name)
        self.comment = json['comment']
        self.type = json["type"]
        if "precedence" in json:
            self.assocPrec = (json["associativity"], json["precedence"])
        else:
            self.assocPrec = None
    
    def get_markdown(self):
        ret = ['<div style="padding: 0px; margin: 0px; width: 980px; height: 1px; background-color: rgb(216, 221, 225);"></div>']
        
        bits =  self.type.split("->")
        
        link = name_link(self.safe_name)+'<span class="mono">'+'<span class="green">-&gt;</span>'.join(bits)+"</span>"
        
        if self.assocPrec:
            link += '<span class="floatright">associativity: <strong>%s</strong> / precedence: <strong>%d</strong> </span>'%self.assocPrec

        ret.append(link)  
        ret.append(self.comment)

        return "\n\n".join(ret)

    markdown = property(get_markdown)

class Module(object):
    def __init__(self, json, package):
        if not json.get('generated-with-elm-version', None):
            json = upgrade_json(json)
        self.package = package
        self.name = json["name"]
        self.safe_name = safe_name(self.name)
        self.comment = json['comment']
        
        self.aliases = {v.name:v for v in map(Alias, json['aliases'])}
        self.types = {v.name:v for v in map(Type, json['types'])}
        self.values = {v.name:v for v in map(Value, json['values'])}
        
    def insert_in_db(self, name, kind):
        file_name = docname(self.package, self.name)
        sname = safe_name(name)
        name = name if name[0] in valid_chars else "(%s)"%name
        
        if not DEBUG:
            cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?,?,?)', (name, kind, file_name+"#"+sname))
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
        
        items = [i.strip() for i in hints.split(",")]
        
        for item in items:
            if item.startswith("docs"): item = item.split()[1]
            if item.startswith("("): item = item[1:-1]

            if item in self.values:
                
                da = self.insert_in_db(self.values[item].name, "Function")
                ret.append(da) #DashAnchor
                ret.append(self.values[item].markdown)
                

            elif item in self.types:
                
                da = self.insert_in_db(self.types[item].name, "Union")
                ret.append(da) #DashAnchor
                ret.append(self.types[item].markdown)
                

            elif item in self.aliases:
                
                da = self.insert_in_db(self.aliases[item].name, "Type")
                ret.append(da) #DashAnchor
                ret.append(self.aliases[item].markdown)
               

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

            print "Error in ", self.package, self.name
            
            import traceback
            traceback.print_exc()

        return  "\n\n".join(ret)

    markdown = property(get_markdown)

def docname(pkg, module=None):
    module = (module if module else "index")
    return ".".join([pkg.replace("/", "."), module, "html"])

def generate_all():
    global pkgs
    print("feching all packages list ..."),
    all_pkgs = fetch(pkgsURL+"all-packages")
    print("DONE!")
    print("feching new packages list ..."),
    new_pkgs = fetch(pkgsURL+"new-packages")
    print("DONE!")

    new_pkgs = list(set(new_pkgs))
    all_pkgs_dict = {p["name"]:p for p in all_pkgs}

    deprecated = [p for p in all_pkgs_dict.iteritems() if not p in new_pkgs]

    pkgs = [p for p in all_pkgs if  p["name"] in new_pkgs]
    pkgs.sort(key=lambda a: a["name"].lower())
    
    # generate the index
    with open(opj(docpath, "index.html"), "w") as fo:
        fo.write(indexTemplate({"pkgs":[(pkg["name"], docname(pkg["name"]), pkg["summary"]) for pkg in pkgs]}))

    no_pkgs = len(pkgs)
    for pkg in pkgs:
        idx = pkgs.index(pkg)+1
        pkg_name = pkg["name"]
        pkg_file = docname(pkg_name)
        pkg_version = pkg["versions"][0]
        print "Generating package: "+pkg_name+" [% 3d / %03d]..."%(idx, no_pkgs), 

        docURL = pkgsURL+"/".join(["packages", pkg_name, pkg_version, "documentation"])+".json"
        json = fetch(docURL)
        # module = Module(json)
        links = []
        for module in json:
            module = Module(module, pkg_name)
            module_file = docname(pkg_name, module.name)
            links.append((module.name, module_file))
            with open(opj(docpath, module_file), "w") as fo:  
                html = toHtml(module.markdown).replace('<code>', '<code class="elm">') # fix syntax detection
                data = { "pkg_link": (pkg_name, pkg_file), "module_name":module.name, "markdown":html}
                fo.write(moduleTemplate(data))
            cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?,?,?)', (module.name, 'Module', module_file))

        with open(opj(docpath, pkg_file), "w") as fo:
            data = { "pkg_name": pkg_name, "modules":links, "version":pkg_version}
            fo.write(pkgTemplate(data))
        cur.execute('INSERT OR IGNORE INTO searchIndex(name, type, path) VALUES (?,?,?)', (pkg_name, 'Package', pkg_file))

        print "DONE!"

DEBUG = False 
# DEBUG = True

if __name__ == '__main__':
    print("starting ...")

    if DEBUG:
        from debug import debug_module
        debug_module("johnpmayer/tagtree", "Data.TagTree")
    else:
        prepare()

        generate_all()
        
        db.commit()
        db.close()

    print("Alright! Take Care Now, Bye Bye Then!")