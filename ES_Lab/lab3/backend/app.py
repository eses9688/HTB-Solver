import subprocess

from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/")
def index():
    return jsonify({"service": "ES Automation Backend", "status": "ok"})


@app.route("/run", methods=["POST"])
def run_code():
    """리포트 자동화 스크립트 실행.

    NOTE(devops): 이 서비스는 internal-net에서만 접근 가능하며 포탈(신뢰된 내부
    호출자)만 호출한다고 가정해 별도 인증을 두지 않았다. (JIRA ES-5011: 재검토 필요)
    """
    data = request.get_json(silent=True) or {}
    code = data.get("code")
    if not code:
        return jsonify({"error": "code required"}), 400

    try:
        result = subprocess.run(
            ["python3"],
            input=code,
            capture_output=True,
            text=True,
            timeout=20,
        )
        return jsonify({
            "returncode": result.returncode,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "script timed out"}), 504


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
