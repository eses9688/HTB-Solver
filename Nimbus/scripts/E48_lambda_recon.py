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
import os, json, subprocess
def handler(event, context):
    out = {}
    try:
        with open("/proc/self/status") as f:
            for line in f:
                if line.startswith("Cap"):
                    out.setdefault("caps", []).append(line.strip())
    except Exception as e:
        out["caps_err"] = str(e)
    try:
        with open("/proc/self/mountinfo") as f:
            out["mountinfo"] = f.read()[:3000]
    except Exception as e:
        out["mountinfo_err"] = str(e)
    for p in ["/var/run/docker.sock", "/run/docker.sock", "/host", "/hostfs"]:
        out[p] = os.path.exists(p)
    out["proc_1_root_readlink"] = subprocess.run(["ls","-la","/proc/1/root/"], capture_output=True, text=True).stdout[:500]
    return out
'''

buf = io.BytesIO()
with zipfile.ZipFile(buf, "w") as z:
    z.writestr("handler.py", code)
buf.seek(0)

try:
    client.delete_function(FunctionName="probe2")
except Exception:
    pass

resp = client.create_function(
    FunctionName="probe2",
    Runtime="python3.11",
    Role="arn:aws:iam::<REDACTED_ACCOUNT_ID>:role/lambda-role",
    Handler="handler.handler",
    Code={"ZipFile": buf.read()},
    Timeout=30,
)
print("CREATED")

time.sleep(3)
inv = client.invoke(FunctionName="probe2", Payload=b"{}")
print("PAYLOAD", inv["Payload"].read().decode())
