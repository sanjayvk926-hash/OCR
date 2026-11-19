
import pymupdf
import cv2
from pathlib import Path

PDF_FILE = "tamil_document_1997.pdf"
OUTPUT_DIR = Path("preprocessed")

OUTPUT_DIR.mkdir(exist_ok=True)

document = pymupdf.open(PDF_FILE)

for index, page in enumerate(document):
    print(f"Preprocessing page {index + 1}/{len(document)}")

    # Render at high resolution
    pix = page.get_pixmap(
        matrix=pymupdf.Matrix(3, 3),
        colorspace=pymupdf.csGRAY,
        alpha=False
    )

    # Convert to OpenCV image
    image = cv2.imdecode(
        __import__("numpy").frombuffer(
            pix.tobytes("png"), dtype="uint8"
        ),
        cv2.IMREAD_GRAYSCALE
    )

    # Remove noise
    denoised = cv2.fastNlMeansDenoising(
        image, None, 10, 7, 21
    )

    # Enhance local contrast
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )
    enhanced = clahe.apply(denoised)

    # Adaptive threshold version
    threshold = cv2.adaptiveThreshold(
        enhanced,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )

    # Save both variants
    cv2.imwrite(
        str(OUTPUT_DIR / f"page_{index+1}_enhanced.png"),
        enhanced
    )

    cv2.imwrite(
        str(OUTPUT_DIR / f"page_{index+1}_threshold.png"),
        threshold
    )

document.close()

print("\nPREPROCESSING COMPLETED!")
print("Check the preprocessed folder.")
