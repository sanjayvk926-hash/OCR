
import fitz
import json
from pathlib import Path
from google.cloud import vision


# ==========================================
# CONFIGURATION
# ==========================================

PDF_FILE = "tamil_document_1997.pdf"
DPI = 300
LANGUAGE = "ta"

OUTPUT_DIR = Path("full_ocr_output")
OUTPUT_DIR.mkdir(exist_ok=True)


# ==========================================
# INITIALIZATION
# ==========================================

print("=" * 55)
print("TAMIL DOCUMENT - FULL OCR")
print("=" * 55)

print(f"Resolution: {DPI} DPI")
print("Colour mode: Original RGB")
print("Preprocessing: None")
print(f"Language: {LANGUAGE}")

client = vision.ImageAnnotatorClient()
document = fitz.open(PDF_FILE)

all_pages_text = []
successful_pages = 0
failed_pages = 0


# ==========================================
# EXTRACT WORDS AND COORDINATES
# ==========================================

def extract_word_data(annotation):

    words_data = []

    for vision_page in annotation.pages:
        for block in vision_page.blocks:
            for paragraph in block.paragraphs:
                for word in paragraph.words:

                    word_text = "".join(
                        symbol.text for symbol in word.symbols
                    )

                    vertices = []

                    for vertex in word.bounding_box.vertices:
                        vertices.append({
                            "x": vertex.x,
                            "y": vertex.y
                        })

                    words_data.append({
                        "text": word_text,
                        "confidence": word.confidence,
                        "vertices": vertices
                    })

    return words_data


# ==========================================
# PROCESS ALL PDF PAGES
# ==========================================

for page_index in range(len(document)):

    page_number = page_index + 1

    print(f"\nProcessing page {page_number}/{len(document)}")

    try:

        # 1. Load original PDF page
        page = document.load_page(page_index)

        page_width = page.rect.width
        page_height = page.rect.height

        # 2. Render at 300 DPI in original RGB colour
        scale = DPI / 72

        pixmap = page.get_pixmap(
            matrix=fitz.Matrix(scale, scale),
            colorspace=fitz.csRGB,
            alpha=False
        )

        image_width = pixmap.width
        image_height = pixmap.height

        # Save original rendered image for verification
        image_path = OUTPUT_DIR / f"page_{page_number}_300dpi.png"
        pixmap.save(str(image_path))

        # 3. Send image to Google Vision
        image_bytes = pixmap.tobytes("png")
        image = vision.Image(content=image_bytes)

        image_context = vision.ImageContext(
            language_hints=[LANGUAGE]
        )

        response = client.document_text_detection(
            image=image,
            image_context=image_context
        )

        if response.error.message:
            raise RuntimeError(response.error.message)

        annotation = response.full_text_annotation

        extracted_text = (
            annotation.text if annotation else ""
        )

        # 4. Save individual page text
        text_path = OUTPUT_DIR / f"page_{page_number}.txt"

        text_path.write_text(
            extracted_text,
            encoding="utf-8"
        )

        # 5. Extract word coordinates
        words_data = []

        if annotation:
            words_data = extract_word_data(annotation)

        # 6. Save JSON data
        page_data = {
            "page_number": page_number,
            "dpi": DPI,
            "color_mode": "RGB",
            "preprocessing": "none",

            "image_dimensions": {
                "width": image_width,
                "height": image_height
            },

            "pdf_page_dimensions": {
                "width_points": page_width,
                "height_points": page_height
            },

            "extracted_text": extracted_text,
            "words": words_data
        }

        json_path = (
            OUTPUT_DIR / f"page_{page_number}_words.json"
        )

        with open(json_path, "w", encoding="utf-8") as file:
            json.dump(
                page_data,
                file,
                ensure_ascii=False,
                indent=4
            )

        all_pages_text.append(
            f"\n\n========== PAGE {page_number} ==========\n\n"
            f"{extracted_text}"
        )

        successful_pages += 1

        print("Status: SUCCESS")
        print(f"Detected words: {len(words_data)}")
        print(f"Characters: {len(extracted_text)}")

    except Exception as error:

        failed_pages += 1

        print(f"Status: FAILED - {error}")

        all_pages_text.append(
            f"\n\n========== PAGE {page_number} FAILED ==========\n"
            f"{error}"
        )


# ==========================================
# SAVE COMBINED OCR TEXT
# ==========================================

combined_text = "".join(all_pages_text)

combined_path = OUTPUT_DIR / "all_pages_ocr.txt"

combined_path.write_text(
    combined_text,
    encoding="utf-8"
)


# ==========================================
# FINAL REPORT
# ==========================================

document.close()

print("\n" + "=" * 55)
print("OCR PROCESS COMPLETED")
print("=" * 55)

print(f"Total pages: {page_number}")
print(f"Successful: {successful_pages}")
print(f"Failed: {failed_pages}")

print(f"\nOutput folder: {OUTPUT_DIR.resolve()}")

print("\nGenerated:")
print("- Individual page images")
print("- Individual page OCR text")
print("- Individual word-coordinate JSON")
print("- Combined OCR text")

print("=" * 55)
