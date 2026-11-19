
import fitz
from google.cloud import vision
from pathlib import Path

PDF_FILE = "tamil_document_1997.pdf"
PAGE_NUMBER = 0

client = vision.ImageAnnotatorClient()

document = fitz.open(PDF_FILE)
page = document.load_page(PAGE_NUMBER)

resolutions = [216, 300, 400]

output_file = "resolution_comparison.txt"

with open(output_file, "w", encoding="utf-8") as output:

    for dpi in resolutions:

        print(f"\nProcessing at {dpi} DPI...")

        # Convert PDF page into an image at selected DPI
        scale = dpi / 72

        pix = page.get_pixmap(
            matrix=fitz.Matrix(scale, scale),
            alpha=False
        )

        image_bytes = pix.tobytes("png")

        image = vision.Image(content=image_bytes)

        response = client.document_text_detection(
            image=image,
            image_context=vision.ImageContext(
                language_hints=["ta"]
            )
        )

        if response.error.message:
            raise RuntimeError(response.error.message)

        text = response.full_text_annotation.text

        print(f"\n===== {dpi} DPI RESULT =====")
        print(text or "No text detected")

        output.write(f"\n\n{'=' * 60}\n")
        output.write(f"RESOLUTION: {dpi} DPI\n")
        output.write(f"{'=' * 60}\n")
        output.write(text or "No text detected")

document.close()

print("\nAll tests completed!")
print(f"Results saved to {output_file}")
