import requests
from botocore.awsrequest import AWSRequest
from botocore.auth import SigV4Auth
from botocore.credentials import Credentials

ACCESS_KEY = "<REDACTED>"
SECRET_KEY = "<REDACTED>"
SESSION_TOKEN = ("<REDACTED_SESSION_TOKEN>")

creds = Credentials(ACCESS_KEY, SECRET_KEY, SESSION_TOKEN)
ENDPOINT = "http://aws.nimbus.htb"
QUEUE_URL = f"{ENDPOINT}/<REDACTED_ACCOUNT_ID>/nimbus-jobs"

url = f"{ENDPOINT}/_aws/sqs/messages?QueueUrl={QUEUE_URL}"
req = AWSRequest(method="GET", url=url)
SigV4Auth(creds, "sqs", "us-east-1").add_auth(req)
prepared = req.prepare()

r = requests.get(prepared.url, headers=dict(prepared.headers), timeout=15)
print("STATUS:", r.status_code)
print("BODY:", r.text[:2000])
