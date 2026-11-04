import pathlib, json, os, sys
p = pathlib.Path('ui/app.py').resolve()
print('file:', p)
print('parents0:', p.parents[0])
print('parents1:', p.parents[1])
print('parents2:', p.parents[2])
