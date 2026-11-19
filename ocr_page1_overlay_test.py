from pathlib import Path
import json
import pymupdf
from google.cloud import vision

# Original 7-page scanned PDF (not the earlier text-only transcription PDF).
PDF_FILE = Path('tamil_document_1997.pdf')
OUTPUT_DIR = Path('ocr_test_output')
OUTPUT_DIR.mkdir(exist_ok=True)

if not PDF_FILE.exists():
    raise FileNotFoundError(
        f"Cannot find {PDF_FILE}. Put this script in the same folder as the original PDF."
    )

# Render original page 1 at 300 DPI. This keeps the source page as the OCR input.
doc = pymupdf.open(PDF_FILE)
if len(doc) < 1:
    raise RuntimeError('The source PDF has no pages.')
page = doc[0]
pix = page.get_pixmap(matrix=pymupdf.Matrix(300 / 72, 300 / 72), colorspace=pymupdf.csRGB, alpha=False)
image_path = OUTPUT_DIR / 'page_1_original_300dpi.png'
pix.save(image_path)

client = vision.ImageAnnotatorClient()
image = vision.Image(content=image_path.read_bytes())
response = client.document_text_detection(
    image=image,
    image_context=vision.ImageContext(language_hints=['ta'])
)
if response.error.message:
    raise RuntimeError(response.error.message)

annotation = response.full_text_annotation
(OUTPUT_DIR / 'page_1_ocr.txt').write_text(annotation.text or '', encoding='utf-8')

# Preserve word-level boxes. These coordinates are in the rendered PNG pixel space.
words = []
for page_index, ocr_page in enumerate(annotation.pages):
    for block_index, block in enumerate(ocr_page.blocks):
        for paragraph_index, paragraph in enumerate(block.paragraphs):
            for word_index, word in enumerate(paragraph.words):
                text = ''.join(symbol.text for symbol in word.symbols)
                vertices = [
                    {'x': v.x, 'y': v.y}
                    for v in word.bounding_box.vertices
                ]
                words.append({
                    'text': text,
                    'vertices': vertices,
                    'block': block_index,
                    'paragraph': paragraph_index,
                    'word': word_index,
                })

result = {
    'source_pdf': PDF_FILE.name,
    'source_page': 1,
    'rendered_image': str(image_path),
    'image_width': pix.width,
    'image_height': pix.height,
    'full_text': annotation.text or '',
    'words': words,
}
(OUTPUT_DIR / 'page_1_ocr_boxes.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8'
)

print('Page 1 OCR test completed.')
print(f'Image: {image_path}')
print(f'Text: {OUTPUT_DIR / "page_1_ocr.txt"}')
print(f'Word coordinates: {OUTPUT_DIR / "page_1_ocr_boxes.json"}')
print('\n--- RECOGNIZED TAMIL TEXT ---\n')
print(annotation.text or '[No text detected]')
print(f'\nDetected words: {len(words)}')
