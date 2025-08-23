# shape_engine.py
from typing import Optional, List, Tuple
from PIL import Image, ImageDraw
from fuzzywuzzy import process
import os

SHAPES: List[str] = ["circle", "square", "triangle", "line", "tree", "house", "sun"]

SYNONYMS = {
    "box": "square",
    "rect": "square",
    "home": "house",
}

def parse_command(cmd: str, mode: str = "strict") -> Optional[str]:
    cmd = (cmd or "").lower().strip()
    if not cmd:
        return None
    if mode == "strict":
        return cmd if cmd in SHAPES else None
    if cmd in SYNONYMS:
        return SYNONYMS[cmd]
    match = process.extractOne(cmd, SHAPES)
    if not match:
        return None
    name, score = match
    return name if score and score > 60 else None

def _polygon_outline(draw: ImageDraw.ImageDraw, points: List[Tuple[int, int]], color: str, width: int):
    for i in range(len(points)):
        p1 = points[i]
        p2 = points[(i + 1) % len(points)]
        draw.line([p1, p2], fill=color, width=width)

def draw_shape(
    shape: str,
    size: Tuple[int, int] = (300, 300),
    stroke: int = 3,
    color: str = "black",
    bg: str = "white",
    filename: str = "outputs/output.png",
) -> str:
    w, h = size
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)

    if shape == "circle":
        draw.ellipse([int(w*0.17), int(h*0.17), int(w*0.83), int(h*0.83)], outline=color, width=stroke)

    elif shape == "square":
        draw.rectangle([int(w*0.17), int(h*0.17), int(w*0.83), int(h*0.83)], outline=color, width=stroke)

    elif shape == "triangle":
        pts = [(int(w*0.50), int(h*0.17)), (int(w*0.17), int(h*0.83)), (int(w*0.83), int(h*0.83))]
        _polygon_outline(draw, pts, color, stroke)

    elif shape == "line":
        draw.line([int(w*0.17), int(h*0.5), int(w*0.83), int(h*0.5)], fill=color, width=stroke)

    elif shape == "tree":
        # trunk
        draw.rectangle([int(w*0.43), int(h*0.62), int(w*0.57), int(h*0.86)], fill="brown")
        # canopy (use requested color)
        pts = [(int(w*0.50), int(h*0.22)), (int(w*0.25), int(h*0.62)), (int(w*0.75), int(h*0.62))]
        draw.polygon(pts, fill=color)
        _polygon_outline(draw, pts, color, 1)

    elif shape == "house":
        draw.rectangle([int(w*0.25), int(h*0.52), int(w*0.75), int(h*0.85)], outline=color, width=stroke)
        pts = [(int(w*0.25), int(h*0.52)), (int(w*0.50), int(h*0.25)), (int(w*0.75), int(h*0.52))]
        _polygon_outline(draw, pts, color, stroke)

    elif shape == "sun":
        # filled circle (sun) using color
        draw.ellipse([int(w*0.25), int(h*0.25), int(w*0.75), int(h*0.75)], fill=color, outline=color, width=stroke)

    else:
        _polygon_outline(draw, [(10, 10), (w-10, 10), (w-10, h-10), (10, h-10)], "red", 2)

    img.save(filename)
    return filename
