
import fitz
from google.cloud import vision

PDF_FILE = "tamil_document_1997.pdf"
PAGE_NUMBER = 0  # Page 1 (Python uses zero-based numbering)

# Open PDF and convert the first page into an image
document = fitz.open(PDF_FILE)
page = document.load_page(PAGE_NUMBER)

pix = page.get_pixmap(matrix=fitz.Matrix(3, 3), alpha=False)
image_bytes = pix.tobytes("png")

# Send image to Google Cloud Vision
client = vision.ImageAnnotatorClient()
image = vision.Image(content=image_bytes)

response = client.document_text_detection(
    image=image,
    image_context=vision.ImageContext(language_hints=["ta"])
)

# Check for API errors
if response.error.message:
    raise RuntimeError(response.error.message)

# Display extracted Tamil text
if response.full_text_annotation.text:
    extracted_text = response.full_text_annotation.text
    print("\n========== TAMIL OCR RESULT ==========\n")
    print(extracted_text)

    with open("page_1_ocr.txt", "w", encoding="utf-8") as file:
        file.write(extracted_text)

    print("\nSaved to page_1_ocr.txt")
else:
    print("No text detected on page 1.")

document.close()
