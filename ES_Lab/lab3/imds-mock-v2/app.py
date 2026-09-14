import uuid

from flask import Flask, request, jsonify, Response

app = Flask(__name__)

ROLE_NAME = "es-automation-role"
VALID_TOKENS = set()

CREDENTIALS = {
    "Code": "Success",
    "Type": "AWS-HMAC",
    "AccessKeyId": "ASIAFAKEESLAB3AUTOM",
    "SecretAccessKey": "FaKeSecretKeyESLab3Automation000000000000",
    "Token": "FAKE.SESSION.TOKEN.ES-LAB3",
    "Note": "esfg{VG05MElIUm9aU0JrWlhOMGFXNWhkR2x2YmlCNVpYUWdMU0IwYUdVZ1ltRmphMlZ1WkNCcGN5QmpZV3hzYVc1bkxnPT0=}",
    "internal-services": {
        "automation-backend": "http://automation-backend:8000/run",
    },
}


@app.route("/latest/api/token", methods=["PUT"])
def get_token():
    if "X-aws-ec2-metadata-token-ttl-seconds" not in request.headers:
        return Response(
            "missing X-aws-ec2-metadata-token-ttl-seconds header", status=400
        )
    token = uuid.uuid4().hex
    VALID_TOKENS.add(token)
    return Response(token, mimetype="text/plain")


def check_token():
    token = request.headers.get("X-aws-ec2-metadata-token")
    return token in VALID_TOKENS


@app.route("/latest/meta-data/iam/security-credentials/")
def role_list():
    if not check_token():
        return Response("401 - use IMDSv2 token via PUT /latest/api/token first", status=401)
    return Response(ROLE_NAME, mimetype="text/plain")


@app.route("/latest/meta-data/iam/security-credentials/<role>")
def role_credentials(role):
    if not check_token():
        return Response("401 - use IMDSv2 token via PUT /latest/api/token first", status=401)
    if role != ROLE_NAME:
        return Response("Not Found", status=404)
    return jsonify(CREDENTIALS)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
