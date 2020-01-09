# elm-docset
Elm Dash Docset generator

To generate, execute `generate.py`. 

Requirements: `pybars3`, `markdown` and `requests`.

You can download the latest version of the docset from User Contributed Section in Dash's Preferences pane. 

To package, execute  `pack.sh`.

## Using Docker
You can build docker image with python and requirements installed
```
docker build -t elm-docset .
```

and then run the script

```
docker run -it --rm --name elm-docset -v "$PWD":/usr/src/app elm-docset python generate.py
```

You can also run packaging script within docker if you would like

```
docker run -it --rm --name elm-docset -v "$PWD":/usr/src/app elm-docset pack.sh 
```
