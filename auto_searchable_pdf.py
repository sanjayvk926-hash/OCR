
import fitz
import json
import csv
from pathlib import Path
from google.cloud import vision


# =====================================================
# 1. CONFIGURATION
# =====================================================

PDF_FILE = Path("tamil_document_1997.pdf")
OUTPUT_PDF = Path("tamil_document_searchable.pdf")

DPI = 300
LANGUAGE = "ta"
COLOR_MODE = "RGB"

OCR_DIR = Path("ocr_data")
OCR_DIR.mkdir(exist_ok=True)

REUSE_EXISTING_OCR = True
LOW_CONFIDENCE_LIMIT = 0.60


# =====================================================
# 2. FIND TAMIL FONT
# =====================================================

def find_tamil_font():

    possible_fonts = [
        Path("Nirmala_0.ttf"),
        Path("Nirmala.ttf"),
        Path("Nirmala UI.ttf"),
        Path(r"C:\Windows\Fonts\Nirmala.ttf"),
        Path(r"C:\Windows\Fonts\Nirmala UI.ttf"),
    ]

    for font_path in possible_fonts:

        if font_path.exists():
            print(f"Tamil font found: {font_path}")
            return str(font_path.resolve())

    raise FileNotFoundError(
        "Tamil font not found. Place Nirmala_0.ttf "
        "inside the project folder."
    )


# =====================================================
# 3. INITIALIZE GOOGLE VISION
# =====================================================

def initialize_vision():

    print("\nConnecting to Google Cloud Vision...")

    client = vision.ImageAnnotatorClient()

    print("Google Vision connected.")

    return client


# =====================================================
# 4. EXTRACT WORDS AND COORDINATES
# =====================================================

def extract_words(annotation):

    words = []

    for vision_page in annotation.pages:

        for block in vision_page.blocks:

            for paragraph in block.paragraphs:

                for word in paragraph.words:

                    text = "".join(
                        symbol.text
                        for symbol in word.symbols
                    )

                    vertices = []

                    for vertex in word.bounding_box.vertices:

                        vertices.append({
                            "x": vertex.x,
                            "y": vertex.y
                        })

                    if not text or len(vertices) != 4:
                        continue

                    words.append({
                        "text": text,
                        "confidence": float(word.confidence),
                        "vertices": vertices
                    })

    return words


# =====================================================
# 5. OCR OR LOAD CACHED OCR
# =====================================================

def get_ocr_data(
    client,
    image_bytes,
    page_number,
    image_width,
    image_height
):

    json_path = OCR_DIR / f"page_{page_number}.json"

    if REUSE_EXISTING_OCR and json_path.exists():

        try:

            with open(json_path, "r", encoding="utf-8") as file:
                cached = json.load(file)

            dimensions = cached["image_dimensions"]

            if (
                cached.get("dpi") == DPI
                and cached.get("color_mode") == COLOR_MODE
                and dimensions["width"] == image_width
                and dimensions["height"] == image_height
            ):

                print("Using saved OCR data.")
                return cached

        except (KeyError, ValueError, json.JSONDecodeError):
            print("Invalid cache. Running OCR again.")

    print("Sending page to Google Vision...")

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

    words = (
        extract_words(annotation) if annotation else []
    )

    data = {
        "page_number": page_number,
        "dpi": DPI,
        "color_mode": COLOR_MODE,

        "image_dimensions": {
            "width": image_width,
            "height": image_height
        },

        "extracted_text": extracted_text,
        "words": words
    }

    with open(json_path, "w", encoding="utf-8") as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=4
        )

    return data


# =====================================================
# 6. ADD INVISIBLE TAMIL TEXT
# =====================================================

def add_invisible_text(
    page,
    words,
    image_width,
    image_height,
    font_path
):

    page_width = page.rect.width
    page_height = page.rect.height

    scale_x = page_width / image_width
    scale_y = page_height / image_height

    inserted = 0
    failed = 0

    font = fitz.Font(fontfile=font_path)

    font_height = font.ascender - font.descender

    if font_height <= 0:
        raise ValueError("Invalid Tamil font metrics.")

    for word in words:

        text = word["text"]
        vertices = word["vertices"]

        xs = [vertex["x"] for vertex in vertices]
        ys = [vertex["y"] for vertex in vertices]

        x0 = min(xs) * scale_x
        x1 = max(xs) * scale_x

        y0 = min(ys) * scale_y
        y1 = max(ys) * scale_y

        width = x1 - x0
        height = y1 - y0

        if width <= 1 or height <= 1:
            failed += 1
            continue

        # Estimate font size using OCR word height.
        font_size = height / font_height

        # Baseline position.
        baseline_y = y0 + font_size * font.ascender

        try:

            page.insert_text(
                point=(x0, baseline_y),
                text=text,
                fontname="tamilfont",
                fontfile=font_path,
                fontsize=font_size,
                render_mode=3,
                overlay=True
            )

            inserted += 1

        except Exception as error:

            failed += 1

            print(
                f"Failed insertion: {text!r} | {error}"
            )

    return inserted, failed


# =====================================================
# 7. GENERATE LOW-CONFIDENCE REPORT
# =====================================================

def save_confidence_report(low_confidence_words):

    report_path = OCR_DIR / "low_confidence_report.csv"

    with open(
        report_path,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "page",
                "text",
                "confidence"
            ]
        )

        writer.writeheader()
        writer.writerows(low_confidence_words)

    return report_path


# =====================================================
# 8. VERIFY GENERATED PDF
# =====================================================

def verify_pdf():

    print("\nVerifying generated PDF...")

    pdf = fitz.open(OUTPUT_PDF)

    verification_results = []

    for page_number, page in enumerate(pdf, start=1):

        extracted = page.get_text("text")

        verification_results.append({
            "page": page_number,
            "characters": len(extracted),
            "has_text": bool(extracted.strip())
        })

        print(
            f"Page {page_number}: "
            f"{len(extracted)} extracted characters"
        )

    pdf.close()

    return verification_results


# =====================================================
# 9. MAIN PROCESS
# =====================================================

def main():

    if not PDF_FILE.exists():

        raise FileNotFoundError(
            f"Original PDF not found: {PDF_FILE}"
        )

    font_path = find_tamil_font()

    client = initialize_vision()

    original = fitz.open(PDF_FILE)

    output = fitz.open()

    total_words = 0
    total_inserted = 0
    total_failed = 0

    low_confidence_words = []

    print("\n" + "=" * 55)
    print("AUTOMATIC SEARCHABLE TAMIL PDF GENERATOR")
    print("=" * 55)

    print(f"Input: {PDF_FILE}")
    print(f"Pages: {len(original)}")
    print(f"Resolution: {DPI} DPI")
    print(f"Colour mode: {COLOR_MODE}")
    print("Preprocessing: None")
    print("Text layer: Invisible")

    # -------------------------------------------------
    # PROCESS EACH PAGE
    # -------------------------------------------------

    for page_index in range(len(original)):

        page_number = page_index + 1

        print(
            f"\nProcessing page "
            f"{page_number}/{len(original)}"
        )

        source_page = original.load_page(page_index)

        page_width = source_page.rect.width
        page_height = source_page.rect.height

        # Render original page at 300 DPI RGB.
        scale = DPI / 72

        pixmap = source_page.get_pixmap(
            matrix=fitz.Matrix(scale, scale),
            colorspace=fitz.csRGB,
            alpha=False
        )

        image_width = pixmap.width
        image_height = pixmap.height

        image_bytes = pixmap.tobytes("png")

        print(
            f"Image: {image_width} x {image_height}"
        )

        # OCR.
        ocr_data = get_ocr_data(
            client,
            image_bytes,
            page_number,
            image_width,
            image_height
        )

        words = ocr_data["words"]

        print(f"Detected words: {len(words)}")

        # Create a clean page with original dimensions.
        new_page = output.new_page(
            width=page_width,
            height=page_height
        )

        # Insert original scan as visible background.
        new_page.insert_image(
            new_page.rect,
            stream=image_bytes
        )

        # Insert invisible Tamil text.
        inserted, failed = add_invisible_text(
            new_page,
            words,
            image_width,
            image_height,
            font_path
        )

        total_words += len(words)
        total_inserted += inserted
        total_failed += failed

        # Collect low-confidence words.
        for word in words:

            if word["confidence"] < LOW_CONFIDENCE_LIMIT:

                low_confidence_words.append({
                    "page": page_number,
                    "text": word["text"],
                    "confidence": word["confidence"]
                })

        print(f"Inserted: {inserted}")
        print(f"Failed: {failed}")

    # -------------------------------------------------
    # SAVE SEARCHABLE PDF
    # -------------------------------------------------

    print("\nSaving searchable PDF...")

    output.save(
        OUTPUT_PDF,
        garbage=4,
        deflate=True
    )

    original.close()
    output.close()

    # -------------------------------------------------
    # SAVE CONFIDENCE REPORT
    # -------------------------------------------------

    report_path = save_confidence_report(
        low_confidence_words
    )

    # -------------------------------------------------
    # VERIFY
    # -------------------------------------------------

    verification_results = verify_pdf()

    verified_pages = sum(
        1 for item in verification_results
        if item["has_text"]
    )

    # -------------------------------------------------
    # FINAL REPORT
    # -------------------------------------------------

    print("\n" + "=" * 55)
    print("PROCESSING COMPLETED")
    print("=" * 55)

    print(f"Total pages: {page_number}")
    print(f"Total OCR words: {total_words}")
    print(f"Inserted words: {total_inserted}")
    print(f"Failed insertions: {total_failed}")

    print(
        f"Low-confidence words: "
        f"{len(low_confidence_words)}"
    )

    print(
        f"Pages containing extractable text: "
        f"{verified_pages}/{page_number}"
    )

    print(f"\nOutput PDF: {OUTPUT_PDF.resolve()}")
    print(f"OCR data: {OCR_DIR.resolve()}")
    print(f"Confidence report: {report_path.resolve()}")

    print("\nNext: Check Tamil text selection and alignment.")


# =====================================================
# 10. EXECUTION
# =====================================================

if __name__ == "__main__":

    try:

        main()

    except Exception as error:

        print("\nPROCESS FAILED")
        print(f"Reason: {error}")

        raise
