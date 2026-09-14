import boto3
import io
import zipfile
import time

ENDPOINT = "http://172.18.0.2:4566"
client = boto3.client(
    "lambda", endpoint_url=ENDPOINT, region_name="us-east-1",
    aws_access_key_id="test", aws_secret_access_key="test",
)

code = '''
import os, json
def handler(event, context):
    out = {}
    out["listdir_root"] = os.listdir("/")
    out["docker_sock"] = os.path.exists("/var/run/docker.sock")
    out["uid"] = os.getuid()
    try:
        out["hostname"] = os.uname().nodename
    except Exception as e:
        out["hostname_err"] = str(e)
    return out
'''

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w") as z:
    z.writestr("handler.py", code)
buf.seek(0)

try:
    client.delete_function(FunctionName="probe")
except Exception:
    pass

resp = client.create_function(
    FunctionName="probe",
    Runtime="python3.11",
    Role="arn:aws:iam::<REDACTED_ACCOUNT_ID>:role/lambda-role",
    Handler="handler.handler",
    Code={"ZipFile": buf.read()},
    Timeout=30,
)
print("CREATED", resp.get("FunctionArn"))

time.sleep(3)
inv = client.invoke(FunctionName="probe", Payload=b"{}")
print("STATUS", inv["StatusCode"])
print("PAYLOAD", inv["Payload"].read())
if "FunctionError" in inv:
    print("FUNCTION_ERROR", inv["FunctionError"])
