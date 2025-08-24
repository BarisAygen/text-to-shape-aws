from typing import Optional, List, Tuple, Dict
from PIL import Image, ImageDraw
from fuzzywuzzy import process
import os, math

SHAPES: List[str] = ["circle","square","triangle","line","tree","house","sun"]
SYNONYMS = {"box":"square","rect":"square","home":"house"}

def parse_command(cmd: str, mode: str = "strict") -> Optional[str]:
    cmd = (cmd or "").lower().strip()
    if not cmd:
        return None
    if mode == "strict":
        return cmd if cmd in SHAPES else None
    if cmd in SYNONYMS:
        return SYNONYMS[cmd]
    m = process.extractOne(cmd, SHAPES)
    if not m:
        return None
    name, score = m
    return name if score and score > 60 else None

def draw_shape(
    shape: str,
    size: Tuple[int,int]=(300,300),
    stroke: int=3,
    color: str="black",
    bg: str="white",
    filename: str="outputs/output.png",
) -> str:
    w,h = size
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    img = Image.new("RGB",(w,h),bg)
    d = ImageDraw.Draw(img)

    if shape=="circle":
        d.ellipse([int(w*.17),int(h*.17),int(w*.83),int(h*.83)], outline=color, width=stroke)
    elif shape=="square":
        d.rectangle([int(w*.17),int(h*.17),int(w*.83),int(h*.83)], outline=color, width=stroke)
    elif shape=="triangle":
        pts=[(int(w*.50),int(h*.17)),(int(w*.17),int(h*.83)),(int(w*.83),int(h*.83))]
        d.polygon(pts, outline=color)
    elif shape=="line":
        d.line([int(w*.17),int(h*.5),int(w*.83),int(h*.5)], fill=color, width=stroke)
    elif shape=="tree":
        d.rectangle([int(w*.43),int(h*.62),int(w*.57),int(h*.86)], fill="brown")
        pts=[(int(w*.50),int(h*.22)),(int(w*.25),int(h*.62)),(int(w*.75),int(h*.62))]
        d.polygon(pts, fill=color)
    elif shape=="house":
        d.rectangle([int(w*.25),int(h*.52),int(w*.75),int(h*.85)], outline=color, width=stroke)
        pts=[(int(w*.25),int(h*.52)),(int(w*.50),int(h*.25)),(int(w*.75),int(h*.52))]
        d.polygon(pts, outline=color)
    elif shape=="sun":
        d.ellipse([int(w*.25),int(h*.25),int(w*.75),int(h*.75)], fill=color, outline=color, width=stroke)
        for k in range(8):
            a=k*math.pi/4; r=int(min(w,h)*.2); cx,cy=int(w*.5),int(h*.5)
            d.line([cx,cy,cx+int(r*1.3*math.cos(a)),cy+int(r*1.3*math.sin(a))], fill=color, width=2)
    else:
        d.rectangle([10,10,w-10,h-10], outline="red", width=2)

    img.save(filename)
    return filename

def _clamp01(v, default=0.5):
    try:
        x=float(v)
        if x<0.0: return 0.0
        if x>1.0: return 1.0
        return x
    except:
        return default

def _bbox(cx, cy, size, W, H):
    s=max(0.05, min(0.95, (size or 0.3)))
    ww=int(W*s*0.35); hh=int(H*s*0.35)
    x=int(cx*W); y=int(cy*H)
    return (x-ww, y-hh, x+ww, y+hh)

def draw_scene(scene: Dict, filename: str="outputs/scene.png") -> str:
    W=int(scene.get("canvas",{}).get("width",640))
    H=int(scene.get("canvas",{}).get("height",640))
    bg=scene.get("canvas",{}).get("bg","white")
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    img=Image.new("RGB",(W,H),bg)
    d=ImageDraw.Draw(img)

    for obj in scene.get("shapes", []):
        shape=str(obj.get("shape","")).lower().strip()
        color=str(obj.get("color","black")).lower().strip() or "black"

        if shape in {"circle","square","triangle"}:
            cx=_clamp01(obj.get("x",0.5))
            cy=_clamp01(obj.get("y",0.5))
            sz=_clamp01(obj.get("size",0.3), default=0.3)
            x1,y1,x2,y2=_bbox(cx,cy,sz,W,H)
            if shape=="circle":
                d.ellipse([x1,y1,x2,y2], outline=color, width=3)
            elif shape=="square":
                d.rectangle([x1,y1,x2,y2], outline=color, width=3)
            else:
                midx=int((x1+x2)/2)
                pts=[(midx,y1),(x1,y2),(x2,y2)]
                d.polygon(pts, outline=color)
        elif shape=="line":
            x1=_clamp01(obj.get("x1",0.2))
            y1=_clamp01(obj.get("y1",0.2))
            x2=_clamp01(obj.get("x2",0.8))
            y2=_clamp01(obj.get("y2",0.8))
            d.line([int(x1*W),int(y1*H),int(x2*W),int(y2*H)], fill=color, width=3)

    img.save(filename)
    return filename
