import base64
import hashlib
import os
import sqlite3

import requests
from flask import Flask, request, session, redirect, jsonify, url_for

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_PATH = "/tmp/portal.db"

REPORT_API_TOKEN = "es-rep-7f3a9c21"
SSRF_BLOCKED_SUBSTR = "169.254.169.254"

SEED_MEMO = """ES 리포트 임포터 - 인수인계 메모

- 리포트 임포터(/api/reports/import)는 X-Report-Token 헤더가 있어야 동작합니다.
- 현재 토큰: es-rep-7f3a9c21
- 점검(보안팀) 확인용: esfg{SXMgdGhpcyB0aGUgZW5kPyBLZWVwIHBpdm90aW5nIHRocm91Z2ggdGhlIHJlcG9ydCBpbXBvcnRlci4=}
- 위 토큰이 유출되면 즉시 회전(rotate)할 것.
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    fresh = not os.path.exists(DB_PATH)
    conn = get_db()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL
        )"""
    )
    if fresh:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("ops_lead", hash_pw(os.urandom(16).hex())),
        )
        conn.execute(
            "INSERT INTO documents (owner_id, title, content) VALUES (?, ?, ?)",
            (1, "인수인계 - 리포트 임포터 접근", SEED_MEMO),
        )
        conn.commit()
    conn.close()


def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()
    conn.close()
    return row


def encode_doc_id(raw_id: int) -> str:
    return base64.urlsafe_b64encode(str(raw_id).encode()).decode()


def decode_doc_id(token: str):
    try:
        return int(base64.urlsafe_b64decode(token.encode()).decode())
    except Exception:
        return None


PAGE_HEADER = """<!doctype html><html><head><meta charset="utf-8">
<title>ES Customer Portal</title></head><body style="font-family:sans-serif;max-width:640px;margin:40px auto;">
<h2>ES Customer Portal</h2>"""
PAGE_FOOTER = "</body></html>"


@app.route("/")
def index():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    return redirect(url_for("documents"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return PAGE_HEADER + """
        <h3>회원가입</h3>
        <form method="post">
          <input name="username" placeholder="username"><br><br>
          <input name="password" type="password" placeholder="password"><br><br>
          <button type="submit">가입</button>
        </form>
        <p><a href="/login">로그인</a></p>
        """ + PAGE_FOOTER

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if not username or not password:
        return "username/password required", 400

    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hash_pw(password)),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return "username already taken", 409

    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    session["user_id"] = row["id"]
    return redirect(url_for("documents"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return PAGE_HEADER + """
        <h3>로그인</h3>
        <form method="post">
          <input name="username" placeholder="username"><br><br>
          <input name="password" type="password" placeholder="password"><br><br>
          <button type="submit">로그인</button>
        </form>
        <p><a href="/register">회원가입</a></p>
        """ + PAGE_FOOTER

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    if not row or row["password_hash"] != hash_pw(password):
        return "invalid credentials", 401
    session["user_id"] = row["id"]
    return redirect(url_for("documents"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/documents", methods=["GET", "POST"])
def documents():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    conn = get_db()
    if request.method == "POST":
        title = request.form.get("title", "제목 없음")
        content = request.form.get("content", "")
        conn.execute(
            "INSERT INTO documents (owner_id, title, content) VALUES (?, ?, ?)",
            (user["id"], title, content),
        )
        conn.commit()

    rows = conn.execute(
        "SELECT * FROM documents WHERE owner_id = ?", (user["id"],)
    ).fetchall()
    conn.close()

    items = "".join(
        f'<li><a href="/api/documents/{encode_doc_id(r["id"])}">{r["title"]}</a> '
        f'(id: <code>{encode_doc_id(r["id"])}</code>)</li>'
        for r in rows
    )
    return PAGE_HEADER + f"""
    <p>로그인: {user['username']} (<a href="/logout">로그아웃</a>)</p>
    <h3>내 문서함</h3>
    <ul>{items}</ul>
    <h4>새 문서 작성</h4>
    <form method="post">
      <input name="title" placeholder="제목"><br><br>
      <textarea name="content" placeholder="내용"></textarea><br><br>
      <button type="submit">저장</button>
    </form>
    <p><a href="/reports">리포트 임포터 →</a></p>
    """ + PAGE_FOOTER


@app.route("/api/documents/<doc_token>")
def api_document(doc_token):
    user = current_user()
    if not user:
        return jsonify({"error": "login required"}), 401

    raw_id = decode_doc_id(doc_token)
    if raw_id is None:
        return jsonify({"error": "invalid id"}), 400

    conn = get_db()
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (raw_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "not found"}), 404

    # NOTE(devops): 소유자 확인 로직은 프론트에서만 처리 중 — 백엔드 강제 검증 티켓 필요
    return jsonify({"id": doc_token, "owner_id": row["owner_id"], "title": row["title"], "content": row["content"]})


@app.route("/reports")
def reports_page():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    return PAGE_HEADER + """
    <h3>리포트 임포터</h3>
    <p>내부 전용 API입니다. <code>X-Report-Token</code> 헤더로 호출하세요.</p>
    <pre>curl -H "X-Report-Token: &lt;token&gt;" \\
  -X POST http://HOST/api/reports/import \\
  -d "url=http://example.com"</pre>
    """ + PAGE_FOOTER


@app.route("/api/reports/_redir")
def report_redirect():
    # 내부 알림/추적용 범용 리다이렉터. 별도 인증 없음.
    target = request.args.get("to", "")
    if not target:
        return "missing 'to'", 400
    return redirect(target, code=302)


@app.route("/api/reports/import", methods=["POST"])
def import_report():
    token = request.headers.get("X-Report-Token", "")
    if token != REPORT_API_TOKEN:
        return jsonify({"error": "invalid or missing X-Report-Token"}), 403

    url = request.form.get("url") or (request.get_json(silent=True) or {}).get("url")
    if not url:
        return jsonify({"error": "url required"}), 400

    if SSRF_BLOCKED_SUBSTR in url:
        return jsonify({"error": "blocked: internal address not allowed"}), 400

    try:
        resp = requests.get(url, timeout=5, allow_redirects=True)
        return jsonify({"status": resp.status_code, "body": resp.text[:4000]})
    except requests.RequestException as e:
        return jsonify({"error": f"fetch failed: {e}"}), 502


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
