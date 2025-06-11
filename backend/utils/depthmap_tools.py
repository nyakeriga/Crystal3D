import numpy as np
from PIL import Image

def generate_depth_map(image_path: str) -> np.ndarray:
    """
    Dummy depth map generator.
    Converts input image to grayscale and returns it as a numpy 2D array.
    Replace with real depth map logic later.
    """
    image = Image.open(image_path).convert("L")  # grayscale
    depth_map = np.array(image) / 255.0  # normalize to 0-1 float
    return depth_map
