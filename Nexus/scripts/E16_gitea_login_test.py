import requests

IP = "10.129.12.96"
HOST = "git.nexus.htb"
BASE = f"http://{IP}"

for user, pw in [("jones", "y27xb3ha!!74GbR"), ("jones", "N27xh!!2ucY04"), ("admin", "y27xb3ha!!74GbR"), ("admin", "N27xh!!2ucY04")]:
    s = requests.Session()
    s.headers.update({"Host": HOST})
    r = s.get(f"{BASE}/user/login", timeout=10)
    import re
    m = re.search(r'name="_csrf" value="([^"]+)"', r.text)
    token = m.group(1) if m else None
    r2 = s.post(f"{BASE}/user/login", data={
        "_csrf": token,
        "user_name": user,
        "password": pw,
    }, timeout=10, allow_redirects=False)
    print(user, pw, "->", r2.status_code, r2.headers.get("Location"), r2.cookies.get_dict())
