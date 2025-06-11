from pathlib import Path
import numpy as np
import ezdxf
import logging
from typing import Union

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def save_as_dxf(points: Union[np.ndarray, list], output_path: Union[str, Path]) -> None:
    """
    Save a 3D point cloud as a DXF file using ezdxf.

    Args:
        points (np.ndarray | list): Array-like of shape (N, 3) representing x, y, z coordinates.
        output_path (str | Path): Output path for the DXF file.

    Raises:
        ValueError: If input shape is not (N, 3).
        IOError: If the file cannot be saved.
    """
    # Convert to NumPy array
    points = np.asarray(points, dtype=np.float32)

    # Validate shape
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError(f"Points should be Nx3 array, got shape {points.shape}")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()

        for x, y, z in points:
            msp.add_point((x, y, z))

        doc.saveas(str(output_path))
        logger.info(f"DXF file saved to {output_path}")

    except IOError as e:
        logger.error(f"Failed to save DXF file: {e}")
        raise

