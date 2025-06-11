import numpy as np
from stl import mesh
import logging
from typing import Union

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def save_as_stl(
    vertices: Union[np.ndarray, list],
    faces: Union[np.ndarray, list],
    filename: str,
    binary: bool = True
) -> None:
    """
    Save a 3D mesh as an STL file (binary or ASCII).

    Args:
        vertices: Nx3 array-like of vertex coordinates.
        faces: Mx3 or Mx4 array-like of indices into vertices array defining faces.
               If faces have 4 vertices, they will be split into two triangles.
        filename: Output STL filename.
        binary: Save as binary STL if True, ASCII STL if False. Default is True.

    Raises:
        ValueError: If input arrays are malformed.
        IOError: If saving the file fails.
    """
    # Convert to numpy arrays
    vertices = np.asarray(vertices, dtype=np.float32)
    faces = np.asarray(faces, dtype=np.int32)

    # Validate shapes
    if vertices.ndim != 2 or vertices.shape[1] != 3:
        raise ValueError(f"Vertices should be Nx3 array, got shape {vertices.shape}")
    if faces.ndim != 2 or faces.shape[1] not in [3, 4]:
        raise ValueError(f"Faces should be Mx3 or Mx4 array, got shape {faces.shape}")

    # Triangulate quads if any
    if faces.shape[1] == 4:
        logger.info("Triangulating quad faces into triangles")
        tri_faces = []
        for face in faces:
            tri_faces.append(face[:3])
            tri_faces.append([face[0], face[2], face[3]])
        faces = np.array(tri_faces, dtype=np.int32)

    # Prepare mesh data array
    num_faces = faces.shape[0]
    data = np.zeros(num_faces, dtype=mesh.Mesh.dtype)

    for i, face in enumerate(faces):
        for j in range(3):
            data['vectors'][i][j] = vertices[face[j], :]

    m = mesh.Mesh(data)
    try:
        m.save(filename, mode=mesh.Mesh.Mode.BINARY if binary else mesh.Mesh.Mode.ASCII)
        logger.info(f"STL file saved successfully to {filename}")
    except IOError as e:
        logger.error(f"Failed to save STL file: {e}")
        raise

