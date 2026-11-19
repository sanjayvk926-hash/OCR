
import cv2
import numpy as np

# Load enhanced grayscale image
image = cv2.imread(
    "preprocessed/page_1_enhanced.png",
    cv2.IMREAD_GRAYSCALE
)

if image is None:
    raise FileNotFoundError("Page 1 image not found")

# Detect foreground pixels
_, binary = cv2.threshold(
    image, 0, 255,
    cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
)

coords = np.column_stack(np.where(binary > 0))

# Estimate document skew
angle = cv2.minAreaRect(coords)[-1]

if angle < -45:
    angle = -(90 + angle)
else:
    angle = -angle

print(f"Detected skew angle: {angle:.2f} degrees")

# Correct the rotation
height, width = image.shape
center = (width // 2, height // 2)

matrix = cv2.getRotationMatrix2D(
    center, angle, 1.0
)

corrected = cv2.warpAffine(
    image,
    matrix,
    (width, height),
    flags=cv2.INTER_CUBIC,
    borderMode=cv2.BORDER_REPLICATE
)

cv2.imwrite("page_1_deskewed.png", corrected)

print("Saved: page_1_deskewed.png")
