import base64
import json
import time
import uuid

import jwt
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

SECRET = "es-devops-console-signing-key-2026"

USERS = {}  # username -> password (in-memory, demo only)
JOBS = {}  # job_id -> job dict (in-memory, demo only)

STAGE1_FLAG = "esfg{VG05MElIbGxkQ0F0SUhSb1pTQmpiMjV6YjJ4bElHaGhjeUJ0YjNKbElIUm9ZVzRnWVNCc2IyZHBiaUJ3WVdkbExnPT0=}"

JOB_POLL_DELAY_SECONDS = 2


def b64url_decode(seg: str) -> bytes:
    padding = "=" * (-len(seg) % 4)
    return base64.urlsafe_b64decode(seg + padding)


def issue_token(username: str, role: str) -> str:
    return jwt.encode({"sub": username, "role": role}, SECRET, algorithm="HS256")


def verify_token(token: str):
    """DevOps 콘솔 JWT 검증.

    NOTE(devops): 레거시 파트너 연동 시스템이 alg=none 토큰을 보내는 문제가 있어
    임시로 허용 중. 파트너 연동 마이그레이션 끝나면 제거할 것 (JIRA ES-4821).
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("malformed token")

    header = json.loads(b64url_decode(parts[0]))
    alg = header.get("alg", "HS256")

    if alg.lower() == "none":
        return json.loads(b64url_decode(parts[1]))

    return jwt.decode(token, SECRET, algorithms=["HS256"])


def get_auth_payload():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[len("Bearer "):]
    try:
        return verify_token(token)
    except Exception:
        return None


def require_staff():
    payload = get_auth_payload()
    if not payload:
        return None, (jsonify({"error": "authentication required"}), 401)
    if payload.get("role") != "staff":
        return None, (jsonify({"error": "staff role required"}), 403)
    return payload, None


@app.route("/")
def index():
    return jsonify({"service": "ES DevOps Portal", "status": "ok"})


@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username") or (request.get_json(silent=True) or {}).get("username")
    password = request.form.get("password") or (request.get_json(silent=True) or {}).get("password")
    if not username or not password:
        return jsonify({"error": "username/password required"}), 400
    if username in USERS:
        return jsonify({"error": "username already taken"}), 409
    USERS[username] = password
    return jsonify({"token": issue_token(username, "customer")})


@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username") or (request.get_json(silent=True) or {}).get("username")
    password = request.form.get("password") or (request.get_json(silent=True) or {}).get("password")
    if USERS.get(username) != password:
        return jsonify({"error": "invalid credentials"}), 401
    return jsonify({"token": issue_token(username, "customer")})


@app.route("/internal/dashboard")
def internal_dashboard():
    payload, err = require_staff()
    if err:
        return err

    return jsonify({
        "welcome": f"안녕하세요, {payload.get('sub', 'staff')}",
        "memo": (
            "ES DevOps 내부 콘솔입니다. 리포트 소스 조회는 비동기 job으로 처리됩니다. "
            "POST /internal/jobs 로 job을 등록하고 GET /internal/jobs/<id> 로 상태를 "
            "폴링하세요 (queued -> done)."
        ),
        "flag": STAGE1_FLAG,
    })


@app.route("/internal/jobs", methods=["POST"])
def create_job():
    _, err = require_staff()
    if err:
        return err

    data = request.get_json(silent=True) or {}
    url = data.get("url")
    if not url:
        return jsonify({"error": "url required"}), 400

    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {
        "status": "queued",
        "url": url,
        "method": data.get("method", "GET"),
        "headers": data.get("headers") or {},
        "body": data.get("body"),
        "created_at": time.time(),
        "result": None,
    }
    return jsonify({"job_id": job_id, "status": "queued"})


@app.route("/internal/jobs/<job_id>")
def poll_job(job_id):
    _, err = require_staff()
    if err:
        return err

    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "not found"}), 404

    if job["status"] == "done":
        return jsonify({"status": "done", "result": job["result"]})

    elapsed = time.time() - job["created_at"]
    if elapsed < JOB_POLL_DELAY_SECONDS:
        return jsonify({"status": "queued"})

    try:
        resp = requests.request(
            job["method"],
            job["url"],
            headers=job["headers"],
            data=job["body"],
            timeout=8,
        )
        job["result"] = {"status_code": resp.status_code, "body": resp.text[:4000]}
        job["status"] = "done"
    except requests.RequestException as e:
        job["status"] = "error"
        job["result"] = {"error": str(e)}

    return jsonify({"status": job["status"], "result": job["result"]})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
