import json
from amazon_music_db import *

d = {}

for x in session.query(Song):
    if '(c)' in x.album:
        if not x.album in d:
            d[x.album] = []
        d[x.album].append(x.uri)

with open('deborah_albums', 'w') as f:
    f.write(json.dumps(d))
