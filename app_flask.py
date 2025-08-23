# app_flask.py
from flask import Flask, request, jsonify
import boto3
import time
import os
import re
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from shape_engine import parse_command, draw_shape
from bedrock_client import parse_text_to_command

# === App & global config ===
app = Flask(__name__)

# ADDED: Global rate limit (can also add per-endpoint overrides)
# BEFORE: no limiter
# NOW:    default 5 requests per minute per client IP
limiter = Limiter(get_remote_address, app=app, default_limits=["5 per minute"])

# ADDED: Make presigned URL TTL configurable via env (fallback 600s)
EXPIRE = int(os.getenv("URL_TTL", "600"))  # BEFORE: hard-coded 600s in endpoints

# CHANGED: allow overriding bucket via env; keeps your previous default
S3_BUCKET = os.getenv("S3_BUCKET", "text2shapebucket")
s3 = boto3.client("s3")

# === Input sanitization ===
# ADDED: simple whitelist to block weird characters / overly long input
SAFE_RE = re.compile(r"^[a-zA-Z0-9 ,._\-]{1,80}$")
def _sanitize(s: str) -> bool:
    return bool(SAFE_RE.match((s or "").strip()))

# (Optional) Healthcheck — ADDED for quick checks / future ALB health probes
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True}), 200


# === /draw (strict/creative, non‑AI) ===
@app.route("/draw", methods=["POST"])
@limiter.limit("5 per minute")  # ADDED: per-endpoint limit (in addition to global)
def draw():
    data = request.get_json(force=True)

    # CHANGED: sanitize inputs
    cmd = (data.get("command") or "").strip()
    mode = (data.get("mode") or "creative").strip()
    if not _sanitize(cmd):
        return jsonify({"error": "invalid input"}), 400

    parsed = parse_command(cmd, mode=mode)
    if not parsed:
        return jsonify({"error": "command not recognized"}), 400

    out_name = f"{int(time.time())}-{parsed}.png"
    local_path = f"/tmp/{out_name}"
    draw_shape(parsed, filename=local_path)

    s3.upload_file(local_path, S3_BUCKET, out_name)

    # CHANGED: use EXPIRE instead of hard-coded 600
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": out_name},
        ExpiresIn=EXPIRE
    )
    return jsonify({"shape": parsed, "url": url, "expires_in": EXPIRE})


# === /ai-draw (Bedrock‑backed) ===
@app.route("/ai-draw", methods=["POST"])
@limiter.limit("5 per minute")  # ADDED: per-endpoint limit
def ai_draw():
    data = request.get_json(force=True)

    # CHANGED: sanitize input
    text = (data.get("text") or "").strip()
    if not _sanitize(text):
        return jsonify({"error": "invalid input"}), 400

    # BEFORE: only fuzzy or strict
    # NOW:    try Bedrock first, then fallback to creative fuzzy
    ai = parse_text_to_command(text)
    if not ai:
        parsed = parse_command(text, mode="creative")
        if not parsed:
            return jsonify({"error": "could not parse"}), 400
        shape, color = parsed, "black"
    else:
        shape, color = ai["shape"], ai.get("color", "black")

    out_name = f"{int(time.time())}-{shape}.png"
    local_path = f"/tmp/{out_name}"
    draw_shape(shape, filename=local_path, color=color)

    s3.upload_file(local_path, S3_BUCKET, out_name)

    # CHANGED: use EXPIRE
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": out_name},
        ExpiresIn=EXPIRE
    )
    return jsonify({"shape": shape, "color": color, "url": url, "expires_in": EXPIRE})


if __name__ == "__main__":
    # unchanged
    app.run(host="0.0.0.0", port=5000)
