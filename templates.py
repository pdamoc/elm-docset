
import pybars
from cgi import escape

import markdown
import markdown.extensions.fenced_code

import requests

gitHub = "https://github.com/"
gitHubRaw = "https://raw.githubusercontent.com"

fenced_code = markdown.extensions.fenced_code.makeExtension()

toHtml = lambda text: markdown.markdown(text, extensions=[fenced_code], output_format="html5")

index = u"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    
    <link href="style.css" media="all" rel="stylesheet">
    <link rel="stylesheet" href="github.css">
    <script src="highlight.pack.js"></script>
    <script>hljs.initHighlightingOnLoad();</script>


    <title>{{title}}</title>
  </head>
  <body>
    
  <div class="center">
    <h1> Packages </h1>
    {{#pkglist pkgs}}{{/pkglist}}
    </div>
  </body>
</html>
"""

package = u"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <link href="style.css" media="all" rel="stylesheet">
    
    <link rel="stylesheet" href="github.css">
    <script src="highlight.pack.js"></script>
    <script>hljs.initHighlightingOnLoad();</script>
    
    <title>{{pkg_name}}</title>
  </head>
  <body>
    <div class="center">
    <span style="font-size:24px;">{{pkg_name}} - version: {{version}}</span>

    <p>for more information visit the package&#39;s <a href="https://github.com/{{pkg_name}}/tree/{{version}}">GitHub page</a></p>

    <p>Package contains the following modules:

    {{#moduleslist modules}}{{/moduleslist}}
    {{{gitRM pkg_name}}}
    </div">
  </body>
</html>

"""

module = u"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <link href="style.css" media="all" rel="stylesheet">
    
    <link rel="stylesheet" href="github.css">
    <script src="highlight.pack.js"></script>
    <script>hljs.initHighlightingOnLoad();</script>
    
    <title>{{module_name}}</title>
  </head>
  <body>
    <div class="center">
    
    <div style="padding-top:10px;"> <span style="font-size:24px">{{{package pkg_link}}} / {{module_name}}</span></div>
    {{{markdown}}}

    </div">
  </body>
</html>

"""

def moduleslist(this, options, items):
    result = [u'<ul class="modulesList">']
    for (name, link) in items:
        result.append(u'<li>')
        result.append(u'<a href="%s">%s</a>'%(link, name))
        result.append(u'</li>')
    result.append(u'</ul>')
    return result



def gitRM(this, name):
  readme = requests.get("/".join([gitHub, name, "raw/master", "README.md"])).text
  result = toHtml(readme)
  return result


def package_helper(this, (name, link)):
  author, package = name.split("/")
  return '<span> %s / <a href="%s">%s</a></span>'%(author, link, package)


def pkglist(this, options, items):
    result = [u'<table>']
    for (name, link, summary) in items:
        result.append(u'<tr>')
        result.append(u'<td class="first"><a href="%s">%s</a></td>'%(link, name))
        result.append(u'<td>%s</td>'%summary)
        result.append(u'</tr>')
    result.append(u'</table>')
    return result

indexTemplate = lambda d: pybars.Compiler().compile(index)(d, helpers={"pkglist":pkglist}).encode("utf-8")
pkgTemplate = lambda d: pybars.Compiler().compile(package)(d, helpers={"moduleslist":moduleslist, "gitRM":gitRM}).encode("utf-8")
moduleTemplate = lambda d: pybars.Compiler().compile(module)(d, helpers={"package":package_helper}).encode("utf-8")
