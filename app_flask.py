from flask import Flask, request, jsonify
import boto3, time, os, json
from shape_engine import draw_shape, draw_scene, parse_command
from bedrock_client import parse_text_to_scene

app = Flask(__name__)
S3_BUCKET = os.getenv("S3_BUCKET","text2shapebucket")
s3 = boto3.client("s3")

@app.post("/ai-draw")
def ai_draw():
    data = request.get_json(force=True)
    text = data.get("text","")
    scene = parse_text_to_scene(text)
    out_name = f"{int(time.time())}.png"
    local = f"/tmp/{out_name}"
    if scene:
        draw_scene(scene, filename=local)
    else:
        cmd = data.get("command","")
        shape = parse_command(cmd, mode="creative")
        draw_shape(shape or "circle", filename=local)
    s3.upload_file(local, S3_BUCKET, out_name)
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": out_name},
        ExpiresIn=600
    )
    return jsonify({"url": url, "expires_in": 600})

@app.post("/draw")
def draw_basic():
    data = request.get_json(force=True)
    cmd = data.get("command","")
    mode = data.get("mode","creative")
    shape = parse_command(cmd, mode=mode)
    if not shape:
        return jsonify({"error":"command not recognized"}), 400
    out_name = f"{int(time.time())}-{shape}.png"
    local = f"/tmp/{out_name}"
    draw_shape(shape, filename=local)
    s3.upload_file(local, S3_BUCKET, out_name)
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": out_name},
        ExpiresIn=600
    )
    return jsonify({"shape": shape, "url": url, "expires_in": 600})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
