from pathlib import Path
import cv2
import numpy as np

def convert_to_grayscale(image_path: Path) -> Path:
    image = cv2.imread(str(image_path))
    
    if image is None:
        raise ValueError(f"Could not load image at: {image_path}")

    # Convert only if image has 3 channels
    if len(image.shape) == 3 and image.shape[2] == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image  # Already grayscale

    output_path = image_path.parent / f"gray_{image_path.stem}.png"
    cv2.imwrite(str(output_path), gray)
    return output_path


def remove_background(image_path: Path) -> Path:
    image = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)

    if image is None:
        raise ValueError(f"Could not load image at: {image_path}")

    # If already grayscale
    if len(image.shape) == 2:
        gray = image
        image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    elif len(image.shape) == 3 and image.shape[2] == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif len(image.shape) == 3 and image.shape[2] == 4:
        # If image has alpha channel
        b, g, r, a = cv2.split(image)
        image = cv2.merge([b, g, r])
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        raise ValueError("Unsupported image format or corrupted file.")

    # Create alpha mask from threshold
    _, alpha = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

    # Split channels again after grayscale fix
    b, g, r = cv2.split(image)
    rgba = cv2.merge([b, g, r, alpha])

    output_path = image_path.parent / f"bg_removed_{image_path.stem}.png"
    cv2.imwrite(str(output_path), rgba)
    return output_path

