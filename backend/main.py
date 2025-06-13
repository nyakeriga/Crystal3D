from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil, uuid
import numpy as np, cv2
from PIL import Image, ImageOps

from backend.utils.image_processing import convert_to_grayscale, remove_background
from backend.utils.dxf_exporter import save_as_dxf
from backend.utils.stl_exporter import save_as_stl
from backend.utils.obj_exporter import OBJExporter

# ────────────────────────────────────────────────
# app & CORS
# ────────────────────────────────────────────────
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # ← in prod, restrict this!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ────────────────────────────────────────────────
# mounts & paths
# ────────────────────────────────────────────────
app.mount("/static",   StaticFiles(directory="static"),   name="static")
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

UPLOAD_DIR  = Path("static/uploads");  UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PREV_DIR    = Path("static/previews"); PREV_DIR.mkdir(parents=True, exist_ok=True)

# ────────────────────────────────────────────────
# helpers
# ────────────────────────────────────────────────
def generate_depth_map(img_path: Path, res: int = 512) -> np.ndarray:
    img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
    img = cv2.resize(img, (res, res), interpolation=cv2.INTER_AREA)
    blur = cv2.GaussianBlur(img, (5, 5), 0)
    return cv2.normalize(blur, None, 0.0, 1.0, cv2.NORM_MINMAX)

def depth_to_points(depth: np.ndarray) -> np.ndarray:
    h, w = depth.shape
    return np.array([[x, y, float(depth[y, x])] for y in range(h) for x in range(w)], np.float32)

def grid_faces(h: int, w: int):
    f = []
    for y in range(h - 1):
        for x in range(w - 1):
            i = y * w + x
            f += [[i, i+1, i+w], [i+1, i+w+1, i+w]]
    return f

# ────────────────────────────────────────────────
# root – serve SPA
# ────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
def spa():
    return HTMLResponse(Path("frontend/index.html").read_text(), 200)

# ────────────────────────────────────────────────
# preview endpoint
# ────────────────────────────────────────────────
@app.post("/preview-depthmap")
async def preview(
    file: UploadFile = File(...),
    bg_color: str = Query("white", regex="^(white|black)$"),
    brightness: int = Query(0), gamma: float = Query(1.0),
    res: int = Query(512, ge=128, le=1024),
):
    try:
        temp = PREV_DIR / f"{uuid.uuid4().hex}_{file.filename}"
        with open(temp, "wb") as buf: shutil.copyfileobj(file.file, buf)

        # composite over bg & grayscale
        with Image.open(temp).convert("RGBA") as im:
            bg_rgba = (255,255,255,255) if bg_color=="white" else (0,0,0,255)
            base = Image.new("RGBA", im.size, bg_rgba)
            gray = ImageOps.grayscale(Image.alpha_composite(base, im))

        gpath = temp.with_suffix(".gray.png"); gray.save(gpath)

        depth = generate_depth_map(gpath, res)
        depth = np.clip(depth*255 + brightness, 0, 255).astype(np.uint8)
        depth = (np.power(depth/255.0, gamma)*255).astype(np.uint8)

        dpath = temp.with_suffix(".depth.png"); cv2.imwrite(str(dpath), depth)

        return {"grayscale_url": f"/download/{gpath.name}",
                "depth_url":      f"/download/{dpath.name}"}

    except Exception as e:
        raise HTTPException(500, f"Preview failed: {e}")

# ────────────────────────────────────────────────
# export endpoint
# ────────────────────────────────────────────────
@app.post("/upload-and-export/{format}/")
async def export(
    format: str,
    file: UploadFile = File(...),
    depth_scale: float = Query(1.0),
    brightness: int = Query(0),
    gamma: float = Query(1.0),
    res: int = Query(512, ge=128, le=1024),
):
    format = format.lower()
    if format not in {"dxf","stl","obj"}:
        raise HTTPException(400, "Unsupported format")

    fpath = UPLOAD_DIR / f"{uuid.uuid4().hex}_{file.filename}"
    with open(fpath, "wb") as buf: shutil.copyfileobj(file.file, buf)

    gray = convert_to_grayscale(fpath)
    no_bg = remove_background(gray)
    depth = generate_depth_map(no_bg, res) * depth_scale

    depth = np.clip(depth*255 + brightness, 0, 255).astype(np.uint8)
    depth = (np.power(depth/255.0, gamma)*255).astype(np.uint8)
    depth = cv2.normalize(depth, None, 0.0, 1.0, cv2.NORM_MINMAX)

    pts   = depth_to_points(depth)
    faces = grid_faces(*depth.shape)

    out = UPLOAD_DIR / f"{fpath.stem}.{format}"
    try:
        if format=="dxf": save_as_dxf(pts, out)
        elif format=="stl": save_as_stl(pts, faces, out)
        else: OBJExporter(pts.tolist(), faces).save(str(out))
    except Exception as e:
        raise HTTPException(500, f"Export failed: {e}")

    return {"message":f"{format.upper()} exported", "file":f"/download/{out.name}"}

# ────────────────────────────────────────────────
# download helper
# ────────────────────────────────────────────────
@app.get("/download/{fname}")
def dl(fname:str):
    p= (UPLOAD_DIR/fname) if (UPLOAD_DIR/fname).exists() else (PREV_DIR/fname)
    if not p.exists(): raise HTTPException(404,"File not found")
    return FileResponse(p, filename=fname)

