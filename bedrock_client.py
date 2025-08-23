import os, json, re, boto3

SHAPES = ["circle", "square", "triangle", "line", "tree", "house", "sun"]

def _extract_json(txt: str):
    m = re.search(r'\{.*\}', txt, flags=re.S|re.M)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except Exception:
        return {}

def parse_text_to_command(text: str) -> dict:
    region = os.getenv("BEDROCK_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
    brt = boto3.client("bedrock-runtime", region_name=region)

    system_prompt = (
        "You convert natural language into a JSON command for a simple shape engine. "
        "Allowed shapes: circle, square, triangle, line, tree, house, sun. "
        "Only return compact JSON, no extra text. Keys: shape (required), color (optional)."
    )

    # Anthropic & Titan ikisi için de 'text' dönen basit bir gövde kurguluyoruz
    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 200,
        "temperature": 0,
        "system": system_prompt,
        "messages": [
            {"role":"user","content":[{"type":"text","text": f"Instruction: {text}\nReturn JSON only."}]}
        ]
    }

    resp = brt.invoke_model(modelId=model_id, body=json.dumps(body))
    out = json.loads(resp["body"].read())
    # Anthropic benzeri modellerde:
    model_text = out.get("content", [{}])[0].get("text", "")
    data = _extract_json(model_text)

    shape = str(data.get("shape","")).lower().strip()
    color = str(data.get("color","black")).lower().strip() or "black"
    if shape not in SHAPES:
        return {}
    return {"shape": shape, "color": color}
