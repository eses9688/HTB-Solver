import boto3
import requests
from botocore.awsrequest import AWSRequest
from botocore.auth import SigV4Auth

ACCESS_KEY = "<REDACTED>"
SECRET_KEY = "<REDACTED>"
SESSION_TOKEN = ("<REDACTED_SESSION_TOKEN>")

from botocore.credentials import Credentials
creds = Credentials(ACCESS_KEY, SECRET_KEY, SESSION_TOKEN)

ENDPOINT = "http://aws.nimbus.htb"
QUEUE_URL = f"{ENDPOINT}/<REDACTED_ACCOUNT_ID>/nimbus-jobs"

body = "Action=SendMessage&QueueUrl=" + QUEUE_URL.replace(":", "%3A").replace("/", "%2F") + \
       "&MessageBody=hello-debug&Version=2012-11-05"

req = AWSRequest(method="POST", url=ENDPOINT + "/", data=body,
                  headers={"Content-Type": "application/x-www-form-urlencoded"})
SigV4Auth(creds, "sqs", "us-east-1").add_auth(req)
prepared = req.prepare()

r = requests.post(prepared.url, headers=dict(prepared.headers), data=prepared.body, timeout=15)
print("STATUS:", r.status_code)
print("BODY:", r.text[:1000])
