from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import shutil
import numpy as np
import cv2
import uuid
from PIL import Image, ImageOps

from backend.utils.image_processing import convert_to_grayscale, remove_background
from backend.utils.depthmap_tools import generate_depth_map
from backend.utils.dxf_exporter import save_as_dxf
from backend.utils.stl_exporter import save_as_stl
from backend.utils.obj_exporter import OBJExporter

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

UPLOAD_DIR = Path("static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.get("/", response_class=HTMLResponse)
def read_root():
    html_path = Path("frontend/index.html")
    if not html_path.exists():
        return HTMLResponse(content="<h1>Frontend not found</h1>", status_code=404)
    return HTMLResponse(content=html_path.read_text(), status_code=200)


def depth_map_to_pointcloud(depth_map: np.ndarray) -> np.ndarray:
    """
    Convert 2D depth map to 3D point cloud (x, y, depth).
    """
    h, w = depth_map.shape
    points = []
    for y in range(h):
        for x in range(w):
            z = depth_map[y, x]
            if z > 0:
                points.append([float(x), float(y), float(z)])
    return np.array(points, dtype=np.float32)


@app.post("/upload-and-export/{format}/")
async def upload_and_export_format(format: str, file: UploadFile = File(...)):
    format = format.lower()
    if format not in {"dxf", "stl", "obj"}:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'dxf', 'stl', or 'obj'.")

    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Image preprocessing
    gray_path = convert_to_grayscale(file_path)
    bg_removed_path = remove_background(gray_path)

    # Generate depth map and convert to 3D point cloud
    depth_map = generate_depth_map(bg_removed_path)
    points = depth_map_to_pointcloud(depth_map)

    output_path = UPLOAD_DIR / f"{file_path.stem}.{format}"

    try:
        if format == "dxf":
            save_as_dxf(points, output_path)
        elif format == "stl":
            if len(points) < 3:
                raise ValueError("Not enough points to generate STL mesh.")
            faces = [[i, (i + 1) % len(points), (i + 2) % len(points)] for i in range(0, len(points) - 2)]
            save_as_stl(points, faces, output_path)
        elif format == "obj":
            if len(points) < 3:
                raise ValueError("Not enough points to generate OBJ mesh.")
            faces = [(i + 1, i + 2, i + 3) for i in range(0, len(points) - 3, 3)]
            exporter = OBJExporter(vertices=points.tolist(), faces=faces)
            exporter.save(str(output_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export: {str(e)}")

    return {
        "message": f"{format.upper()} file generated successfully",
        "file": f"/download/{output_path.name}"
    }


@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(path=file_path, filename=filename)


@app.post("/preview-depthmap")
async def preview_depthmap(
    file: UploadFile = File(...),
    bg_color: str = Query("white", regex="^(white|black)$")
):
    """
    Generate grayscale + depth map preview for images with transparency.
    Query param: bg_color=white or black
    """
    try:
        input_path = UPLOAD_DIR / f"preview_{uuid.uuid4().hex}_{file.filename}"
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Load image and apply transparent background onto specified color
        with Image.open(input_path).convert("RGBA") as img:
            bg_rgba = (255, 255, 255, 255) if bg_color == "white" else (0, 0, 0, 255)
            background = Image.new("RGBA", img.size, bg_rgba)
            composited = Image.alpha_composite(background, img)
            grayscale = ImageOps.grayscale(composited)

        # Save grayscale
        gray_path = input_path.with_suffix(".gray.png")
        grayscale.save(gray_path)

        # Generate depth map
        depth_array = generate_depth_map(gray_path)
        depth_normalized = cv2.normalize(depth_array, None, 0, 255, cv2.NORM_MINMAX)
        depth_uint8 = depth_normalized.astype(np.uint8)
        depth_png_path = input_path.with_suffix(".depth.png")
        cv2.imwrite(str(depth_png_path), depth_uint8)

        return {
            "grayscale_url": f"/download/{gray_path.name}",
            "depth_url": f"/download/{depth_png_path.name}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Depth map preview failed: {str(e)}")

