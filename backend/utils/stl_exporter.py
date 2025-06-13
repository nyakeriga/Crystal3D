import numpy as np
from stl import mesh, Mode          # ← import Mode for save() options
import logging
from typing import Union

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def save_as_stl(
    vertices: Union[np.ndarray, list],
    faces:    Union[np.ndarray, list],
    filename: str,
    binary:   bool = True
) -> None:
    """
    Save a 3‑D surface mesh to STL.

    Args
    ----
    vertices : (N, 3) float‑like  – XYZ coordinates.
    faces    : (M, 3) int‑like    – indices into vertices (triangles).
    filename : str                – output path (e.g. *.stl).
    binary   : bool               – True → binary STL, False → ASCII.
    """
    # ── prepare data ───────────────────────────────────────────────────────────
    vertices = np.asarray(vertices, dtype=np.float32)
    faces    = np.asarray(faces,    dtype=np.int32)

    logger.info("Building STL mesh (%d vertices, %d faces)…",
                len(vertices), len(faces))

    stl_mesh = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
    for i, tri in enumerate(faces):
        for j in range(3):
            stl_mesh.vectors[i][j] = vertices[tri[j]]

    # ── save ───────────────────────────────────────────────────────────────────
    mode = Mode.BINARY if binary else Mode.ASCII     # <— the right constants
    stl_mesh.save(filename, mode=mode)

    logger.info("STL saved → %s  (%s)", filename,
                "binary" if binary else "ASCII")

