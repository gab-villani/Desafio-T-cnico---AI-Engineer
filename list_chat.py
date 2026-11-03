import pathlib
p = pathlib.Path('chat_history')
print('exists', p.exists())
files = list(p.glob('*.json')) if p.exists() else []
print('count', len(files))
for f in files:
    print(f.name)