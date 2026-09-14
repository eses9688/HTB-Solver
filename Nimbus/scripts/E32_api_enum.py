import requests

paths = [
    "/api/v1/jobs", "/api/v1/job", "/api/v1/submit", "/api/v1/queue",
    "/api/v1/jobs/submit", "/api/v1/health", "/api/v1/status",
    "/api/v1/workers", "/api/v1/version", "/api/v1/config",
    "/api/v1/internal", "/api/v1/debug", "/api/v1/admin",
]

for p in paths:
    try:
        r = requests.get(f"http://nimbus.htb{p}", timeout=8)
        print(f"{p:30s} -> {r.status_code} len={len(r.text)}")
    except Exception as e:
        print(f"{p:30s} -> ERR {e}")
