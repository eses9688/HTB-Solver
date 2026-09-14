from flask import Flask, jsonify, Response

app = Flask(__name__)

ROLE_NAME = "es-portal-role"

CREDENTIALS = {
    "Code": "Success",
    "LastUpdated": "2026-09-07T00:00:00Z",
    "Type": "AWS-HMAC",
    "AccessKeyId": "ASIAFAKEESPORTAL01",
    "SecretAccessKey": "FaKeSecretKeyESLab2Portal0000000000000000",
    "Token": "FAKE.SESSION.TOKEN.ES-LAB2",
    "Expiration": "2026-09-08T00:00:00Z",
    "Note": "esfg{V2VsbCBkb25lISBFUyBQb3J0YWwgTGFiMiBjbGVhci4=}",
}


@app.route("/latest/meta-data/iam/security-credentials/")
def role_list():
    return Response(ROLE_NAME, mimetype="text/plain")


@app.route("/latest/meta-data/iam/security-credentials/<role>")
def role_credentials(role):
    if role != ROLE_NAME:
        return "Not Found", 404
    return jsonify(CREDENTIALS)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
