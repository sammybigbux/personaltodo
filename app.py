import os
import json
from flask import Flask, request, jsonify, send_from_directory

import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__, static_folder="public", static_url_path="")

DATABASE_URL = os.environ["DATABASE_URL"]


def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    conn.autocommit = True
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_state (
            user_id TEXT PRIMARY KEY,
            state JSONB NOT NULL DEFAULT '{"tasks":[],"nextId":1}'::jsonb,
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    cur.close()
    conn.close()


@app.route("/api/state", methods=["GET"])
def get_state():
    user_id = request.headers.get("x-user-id")
    if not user_id:
        return jsonify(error="Missing x-user-id header"), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT state FROM user_state WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row is None:
        return jsonify(tasks=[], nextId=1)
    return jsonify(row["state"])


@app.route("/api/state", methods=["PUT"])
def put_state():
    user_id = request.headers.get("x-user-id")
    if not user_id:
        return jsonify(error="Missing x-user-id header"), 400

    body = request.get_json(silent=True)
    if not body or not isinstance(body.get("tasks"), list) or not isinstance(body.get("nextId"), (int, float)):
        return jsonify(error="Invalid body: need {tasks: [], nextId: number}"), 400

    state = json.dumps({"tasks": body["tasks"], "nextId": body["nextId"]})

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO user_state (user_id, state, updated_at)
        VALUES (%s, %s, NOW())
        ON CONFLICT (user_id) DO UPDATE SET state = %s, updated_at = NOW()
    """, (user_id, state, state))
    cur.close()
    conn.close()

    return jsonify(ok=True)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    return send_from_directory("public", "index.html")


with app.app_context():
    init_db()
