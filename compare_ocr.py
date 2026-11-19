
import fitz
from google.cloud import vision
from pathlib import Path

client = vision.ImageAnnotatorClient()

# METHOD 1: With fitz
doc = fitz.open("tamil_document_1997.pdf")
page = doc.load_page(0)

pix = page.get_pixmap(
    matrix=fitz.Matrix(300 / 72, 300 / 72),
    alpha=False
)

image_with_fitz = pix.tobytes("png")
doc.close()

# METHOD 2: Without fitz
image_without_fitz = Path(
    "ocr_test_output/page_1_original_300dpi.png"
).read_bytes()

files = [
    ("WITH FITZ", image_with_fitz),
    ("WITHOUT FITZ", image_without_fitz)
]

with open("page3_fitz_comparison.txt", "w", encoding="utf-8") as output:

    for name, image_bytes in files:

        print(f"\nProcessing: {name}")

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

        print(f"\n===== {name} =====")
        print(text or "No text detected")

        output.write(f"\n\n{'=' * 60}\n")
        output.write(f"{name}\n")
        output.write(text or "No text detected")

print("\nComparison saved to page3_fitz_comparison.txt")
