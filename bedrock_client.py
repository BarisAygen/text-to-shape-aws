# bedrock_client.py
import os, json, re, boto3
from math import isfinite

PRIMS = {"circle", "square", "triangle", "line"}

# ----- Color normalization (fix Pillow-unsupported names like "peach") -----
SAFE_COLORS = {
    "black","white","red","green","blue","yellow","orange",
    "purple","pink","brown","gray","grey","lightblue","lightgreen",
    "peachpuff","gold","navy","teal","maroon","olive"
}
COLOR_MAP = {
    "peach": "peachpuff",
    "skin": "peachpuff",
    "skin-tone": "peachpuff",
    "beige": "peachpuff",
    "azure": "lightblue",
    "lime": "green",
    "grey": "gray"
}
def _norm_color(c: str) -> str:
    c = (c or "black").strip().lower()
    if c in SAFE_COLORS:
        return c
    if c in COLOR_MAP:
        return COLOR_MAP[c]
    # allow simple hex like #RGB or #RRGGBB
    if c.startswith("#") and len(c) in (4,7):
        return c
    return "black"

# ----- Helpers -----
def _extract_json(s: str):
    m = re.search(r"\{.*\}", s, flags=re.S)
    return json.loads(m.group(0)) if m else {}

def _clamp01(v, default=0.5):
    try:
        x = float(v)
        if not isfinite(x): return default
        if x < 0.0: return 0.0
        if x > 1.0: return 1.0
        return x
    except Exception:
        return default

def _snap(v, step=0.05):
    v = _clamp01(v)
    return round(v / step) * step

def _valid_shape(obj: dict) -> bool:
    shp = str(obj.get("shape","")).lower().strip()
    if shp not in PRIMS:
        return False
    if shp in {"circle","square","triangle"}:
        return all(k in obj for k in ("x","y","size"))
    if shp == "line":
        return all(k in obj for k in ("x1","y1","x2","y2"))
    return False

# ----- Post-process / Normalizer -----
def _sanitize(scene: dict, max_shapes: int = 12) -> dict:
    canvas = scene.get("canvas", {}) or {}
    W = int(canvas.get("width", 640))
    H = int(canvas.get("height", 640))
    bg = str(canvas.get("bg", "lightblue"))

    cleaned = []
    for s in (scene.get("shapes", []) or []):
        if not _valid_shape(s):
            continue
        s = dict(s)
        shp = s["shape"] = s["shape"].lower().strip()
        s["color"] = _norm_color(s.get("color","black"))

        if shp in {"circle","square","triangle"}:
            x = _snap(s.get("x", 0.5))
            y = _snap(s.get("y", 0.5))
            size = _clamp01(s.get("size", 0.25))
            if size < 0.10: size = 0.10
            if size > 0.50: size = 0.50
            x = min(0.90, max(0.10, x))
            y = min(0.90, max(0.10, y))
            s.update({"x":x, "y":y, "size":size})
        else:
            x1 = _snap(s.get("x1", 0.2)); y1 = _snap(s.get("y1", 0.2))
            x2 = _snap(s.get("x2", 0.8)); y2 = _snap(s.get("y2", 0.8))
            s.update({"x1":x1, "y1":y1, "x2":x2, "y2":y2})

        cleaned.append(s)

    cleaned = cleaned[:max_shapes]
    return {"canvas":{"width":W,"height":H,"bg":bg}, "shapes": cleaned}

# ----- Bedrock call -----
def parse_text_to_scene(text: str) -> dict:
    """
    Convert free text into a primitives-only scene JSON.
    """
    region = os.getenv("BEDROCK_REGION", os.getenv("AWS_DEFAULT_REGION","us-east-1"))
    model_id = os.getenv("BEDROCK_MODEL_ID","anthropic.claude-3-haiku-20240307-v1:0")
    brt = boto3.client("bedrock-runtime", region_name=region)

    # Strong system prompt with few-shot and color whitelist
    system = (
        "You strictly convert user requests into a JSON scene using ONLY primitives: "
        "circle, square, triangle, line. NO labels like person/bird/car/heart. "
        "Decompose complex ideas into multiple primitives on a 0..1 normalized canvas.\n\n"
        "Allowed colors: black, white, red, green, blue, yellow, orange, purple, pink, "
        "brown, gray, lightblue, lightgreen, peachpuff, gold, navy, teal, maroon, olive. "
        "If unsure, use black.\n\n"
        "Schema:\n"
        "{\n"
        '  \"canvas\": {\"width\": <int>, \"height\": <int>, \"bg\": \"<string>\"},\n'
        '  \"shapes\": [\n'
        '    {\"shape\":\"circle|square|triangle\", \"color\":\"<string>\", \"x\":0..1, \"y\":0..1, \"size\":0..1},\n'
        '    {\"shape\":\"line\", \"color\":\"<string>\", \"x1\":0..1, \"y1\":0..1, \"x2\":0..1, \"y2\":0..1}\n'
        "  ]\n"
        "}\n\n"
        "Hard rules:\n"
        "- JSON ONLY. No prose, markdown, or comments.\n"
        "- Use <= 12 shapes total.\n"
        "- Prefer symmetry and non-overlapping placement.\n"
        "- Avoid tiny primitives (size < 0.08). Keep important shapes within 0.15..0.85 on both axes.\n\n"
        "Examples:\n"
        "INPUT: draw a house with the sun\n"
        "OUTPUT: {\"canvas\":{\"width\":640,\"height\":640,\"bg\":\"lightblue\"},\"shapes\":["
        "{\"shape\":\"square\",\"color\":\"saddlebrown\",\"x\":0.28,\"y\":0.70,\"size\":0.40},"
        "{\"shape\":\"triangle\",\"color\":\"black\",\"x\":0.28,\"y\":0.48,\"size\":0.40},"
        "{\"shape\":\"circle\",\"color\":\"yellow\",\"x\":0.80,\"y\":0.18,\"size\":0.18}]}\n\n"
        "INPUT: two figures holding hands and a path\n"
        "OUTPUT: {\"canvas\":{\"width\":640,\"height\":640,\"bg\":\"lightblue\"},\"shapes\":["
        "{\"shape\":\"circle\",\"color\":\"peachpuff\",\"x\":0.42,\"y\":0.32,\"size\":0.10},"
        "{\"shape\":\"square\",\"color\":\"blue\",\"x\":0.42,\"y\":0.48,\"size\":0.16},"
        "{\"shape\":\"circle\",\"color\":\"peachpuff\",\"x\":0.58,\"y\":0.32,\"size\":0.10},"
        "{\"shape\":\"square\",\"color\":\"red\",\"x\":0.58,\"y\":0.48,\"size\":0.16},"
        "{\"shape\":\"line\",\"color\":\"black\",\"x1\":0.20,\"y1\":0.85,\"x2\":0.80,\"y2\":0.85}]}\n\n"
        "INPUT: a tree and the sun\n"
        "OUTPUT: {\"canvas\":{\"width\":640,\"height\":640,\"bg\":\"lightblue\"},\"shapes\":["
        "{\"shape\":\"triangle\",\"color\":\"green\",\"x\":0.30,\"y\":0.50,\"size\":0.35},"
        "{\"shape\":\"square\",\"color\":\"brown\",\"x\":0.30,\"y\":0.70,\"size\":0.12},"
        "{\"shape\":\"circle\",\"color\":\"yellow\",\"x\":0.82,\"y\":0.16,\"size\":0.16}]}"
    )

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 450,
        "temperature": 0,
        "system": system,
        "messages": [{"role":"user","content":[{"type":"text","text": text}]}],
    }

    resp = brt.invoke_model(modelId=model_id, body=json.dumps(body))
    raw = json.loads(resp["body"].read())
    txt = (raw.get("content") or [{}])[0].get("text","")

    # First attempt
    scene = _extract_json(txt) or {}
    scene = _sanitize(scene)

    # If empty, retry with a stricter message
    if not scene.get("shapes"):
        retry_body = dict(body)
        retry_body["messages"] = [{"role":"user","content":[{"type":"text","text":
            "Previous output invalid. Return JSON ONLY per schema with <= 12 primitives and allowed colors."}]}]
        resp2 = brt.invoke_model(modelId=model_id, body=json.dumps(retry_body))
        raw2 = json.loads(resp2["body"].read())
        txt2 = (raw2.get("content") or [{}])[0].get("text","")
        scene = _sanitize(_extract_json(txt2) or {})

    return scene if scene.get("shapes") else {}
