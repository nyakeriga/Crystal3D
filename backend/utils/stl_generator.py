from pathlib import Path
import numpy as np
import open3d as o3d
import cv2

def generate_stl(image_path: Path, size=(50, 50, 50), output_format="stl") -> Path:
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError("Image could not be loaded.")

    # Resize image to match crystal face size (width x height)
    width_mm, height_mm, depth_mm = size
    img_resized = cv2.resize(img, (width_mm, height_mm))

    # Normalize depth (grayscale to Z-height)
    z_data = (img_resized / 255.0) * depth_mm
    points = []

    for y in range(img_resized.shape[0]):
        for x in range(img_resized.shape[1]):
            z = z_data[y, x]
            points.append([x, y, z])

    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)

    mesh = o3d.geometry.TriangleMesh.create_from_point_cloud_alpha_shape(pcd, alpha=1.5)
    mesh.compute_vertex_normals()

    output_file = image_path.parent / f"output_model.{output_format}"
    if output_format == "stl":
        o3d.io.write_triangle_mesh(str(output_file), mesh)
    elif output_format == "obj":
        o3d.io.write_triangle_mesh(str(output_file), mesh, write_triangle_uvs=True)
    elif output_format == "dxf":
        raise NotImplementedError("DXF export is not yet supported.")
    else:
        raise ValueError("Unsupported output format.")

    return output_file
