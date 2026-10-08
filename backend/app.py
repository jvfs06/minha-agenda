"""Minha Agenda API: authentication and opt-in revisioned sync foundation."""
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

from flask import Flask, g, jsonify, request, make_response
from flask_cors import CORS

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:
    psycopg = None
    dict_row = None

DATABASE_URL = os.getenv("DATABASE_URL", "")
DB_PATH = os.getenv("AGENDA_DATABASE", str(Path(__file__).with_name("agenda.sqlite3")))
ORIGINS = [x.strip() for x in os.getenv("AGENDA_ALLOWED_ORIGINS", "http://localhost:8000").split(",") if x.strip()]
SECURE_COOKIES = os.getenv("AGENDA_SECURE_COOKIES", "1") == "1"
COOKIE_NAME = "agenda_session"
SESSION_SECONDS = 60 * 60 * 24 * 14
MAX_ITEMS = 500
MAX_PAYLOAD = 64 * 1024
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
CORS(app, origins=ORIGINS, supports_credentials=True)

class PostgresAdapter:
    def __init__(self, conn):
        self.conn = conn
    def execute(self, sql, params=()):
        return self.conn.execute(sql.replace("?", "%s"), params)
    def executescript(self, sql):
        for statement in sql.split(";"):
            if statement.strip():
                self.execute(statement)
    def commit(self):
        self.conn.commit()
    def rollback(self):
        self.conn.rollback()
    def close(self):
        self.conn.close()

@contextmanager
def connect():
    if DATABASE_URL:
        if psycopg is None:
            raise RuntimeError("Instale psycopg para usar DATABASE_URL")
        db = PostgresAdapter(psycopg.connect(DATABASE_URL, row_factory=dict_row))
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
        return

    db = sqlite3.connect(DB_PATH, timeout=15)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    if not DATABASE_URL:
        Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users(
          id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE,
          password_hash TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions(
          token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          expires_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS items(
          user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
          collection TEXT NOT NULL CHECK(collection IN ('records','settings')),
          item_id TEXT NOT NULL, payload TEXT NOT NULL,
          revision INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT NULL,
          PRIMARY KEY(user_id,collection,item_id)
        );
        """)

def hash_password(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000)
    return salt.hex() + ":" + digest.hex()

def verify_password(password, stored):
    try:
        salt_hex, digest_hex = stored.split(":")
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 600_000)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False

def error(message, status):
    return jsonify(error=message), status

def session_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()

def issue_session(user_id):
    token = secrets.token_urlsafe(48)
    with connect() as db:
        db.execute("INSERT INTO sessions VALUES(?,?,?)", (session_hash(token), user_id, int(time.time()) + SESSION_SECONDS))
    return token

def set_session_cookie(response, token):
    response.set_cookie(COOKIE_NAME, token, max_age=SESSION_SECONDS, httponly=True,
                        secure=SECURE_COOKIES, samesite="None" if SECURE_COOKIES else "Lax", path="/")
    return response

def require_user(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        token = request.cookies.get(COOKIE_NAME, "")
        if not token:
            return error("Não autenticado", 401)
        with connect() as db:
            user = db.execute("""SELECT u.id,u.email FROM users u JOIN sessions s ON s.user_id=u.id
               WHERE s.token_hash=? AND s.expires_at>?""", (session_hash(token), int(time.time()))).fetchone()
        if user is None:
            return error("Sessão inválida ou expirada", 401)
        g.user_id, g.email = user["id"], user["email"]
        return fn(*args, **kwargs)
    return inner

@app.before_request
def protect_mutations():
    # Prevent cross-site form and script requests from untrusted origins.
    if request.method in ("POST", "PUT", "PATCH", "DELETE"):
        origin = request.headers.get("Origin")
        if origin not in ORIGINS:
            return error("Origem não permitida", 403)
        if request.mimetype != "application/json":
            return error("Content-Type deve ser application/json", 415)

@app.get("/api/health")
def health():
    return jsonify(status="ok")

def credentials():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    email, password = data.get("email"), data.get("password")
    if not isinstance(email, str) or not isinstance(password, str):
        return None
    email = email.strip().lower()
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or len(password) < 12 or len(password) > 128:
        return None
    return email, password

@app.post("/api/auth/register")
def register():
    creds = credentials()
    if not creds:
        return error("Informe e-mail válido e senha de 12 a 128 caracteres", 400)
    email, password = creds
    user_id = str(uuid.uuid4())
    try:
        with connect() as db:
            db.execute("INSERT INTO users VALUES(?,?,?,?)", (user_id, email, hash_password(password), datetime.now(timezone.utc).isoformat()))
    except Exception as exc:
        if isinstance(exc, sqlite3.IntegrityError) or (psycopg and isinstance(exc, psycopg.errors.UniqueViolation)):
            return error("Não foi possível cadastrar esta conta", 409)
        raise
    token = issue_session(user_id)
    return set_session_cookie(make_response(jsonify(id=user_id, email=email), 201), token)

@app.post("/api/auth/login")
def login():
    creds = credentials()
    if not creds:
        return error("Credenciais inválidas", 401)
    email, password = creds
    with connect() as db:
        user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if user is None or not verify_password(password, user["password_hash"]):
        return error("Credenciais inválidas", 401)
    return set_session_cookie(make_response(jsonify(id=user["id"], email=email)), issue_session(user["id"]))

@app.get("/api/auth/me")
@require_user
def me():
    return jsonify(id=g.user_id, email=g.email)

@app.post("/api/auth/logout")
@require_user
def logout():
    token = request.cookies.get(COOKIE_NAME, "")
    with connect() as db:
        db.execute("DELETE FROM sessions WHERE token_hash=?", (session_hash(token),))
    response = make_response(jsonify(ok=True))
    response.delete_cookie(COOKIE_NAME, path="/", secure=SECURE_COOKIES, samesite="None" if SECURE_COOKIES else "Lax")
    return response

@app.get("/api/sync/<collection>")
@require_user
def pull(collection):
    if collection not in ("records", "settings"):
        return error("Coleção inválida", 404)
    with connect() as db:
        rows = db.execute("SELECT item_id,payload,revision,updated_at FROM items WHERE user_id=? AND collection=? ORDER BY item_id", (g.user_id, collection)).fetchall()
    return jsonify(items=[dict(id=r["item_id"], data=json.loads(r["payload"]), revision=r["revision"], updated_at=r["updated_at"]) for r in rows])

@app.put("/api/sync/<collection>/<item_id>")
@require_user
def push(collection, item_id):
    if collection not in ("records", "settings") or not 1 <= len(item_id) <= 160:
        return error("Item inválido", 400)
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get("data"), dict) or not isinstance(data.get("base_revision"), int):
        return error("Envie data e base_revision", 400)
    if data["base_revision"] < 0 or len(json.dumps(data["data"], ensure_ascii=False)) > MAX_PAYLOAD:
        return error("Conteúdo inválido ou muito grande", 400)
    expected_key = "id" if collection == "records" else "key"
    if data["data"].get(expected_key) != item_id:
        return error("ID do conteúdo não corresponde ao item", 400)
    now = datetime.now(timezone.utc).isoformat()
    with connect() as db:
        lock = " FOR UPDATE" if DATABASE_URL else ""
        current = db.execute("SELECT revision,payload FROM items WHERE user_id=? AND collection=? AND item_id=?" + lock, (g.user_id, collection, item_id)).fetchone()
        revision = current["revision"] if current else 0
        if data["base_revision"] != revision:
            return jsonify(error="Conflito de revisão", current=dict(revision=revision, data=json.loads(current["payload"])) if current else None), 409
        new_revision = revision + 1
        db.execute("""INSERT INTO items(user_id,collection,item_id,payload,revision,updated_at)
                      VALUES(?,?,?,?,?,?) ON CONFLICT(user_id,collection,item_id)
                      DO UPDATE SET payload=excluded.payload,revision=excluded.revision,updated_at=excluded.updated_at""",
                   (g.user_id, collection, item_id, json.dumps(data["data"], ensure_ascii=False), new_revision, now))
    return jsonify(id=item_id, revision=new_revision, updated_at=now)

init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
