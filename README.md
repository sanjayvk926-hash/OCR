# Tamil OCR – Searchable PDF

A Python project for extracting Tamil text from scanned PDF documents using Google Cloud Vision OCR and generating a searchable PDF with an invisible text layer.

## Project goal

The goal is to preserve the scanned document's visual appearance while adding machine-readable Tamil text so users can select, copy, extract, and search the recognised text.

> **Current status:** The workflow has been developed and tested on a seven-page scanned Tamil document. Tamil copy-and-paste/Unicode mapping and final visual alignment still require validation. OCR may contain errors, especially with handwriting, faded text, stamps, and low-quality scans.

## Workflow

1. Read the source PDF.
2. Render each page as a high-resolution image.
3. Send page images to Google Cloud Vision with the Tamil language hint (`ta`).
4. Extract recognised text, confidence values, and bounding-box coordinates.
5. Save OCR results as JSON/text files for reuse and review.
6. Add recognised text as an invisible text layer over the scanned page.
7. Save the searchable PDF and validate extraction, search, alignment, and appearance.

## Technology stack

- Python
- Google Cloud Vision API
- PyMuPDF
- OpenCV
- Pillow
- NumPy
- FontTools
- ReportLab (used during PDF-generation experiments)

## Configuration used during development

| Setting | Value |
|---|---|
| OCR language hint | `ta` (Tamil) |
| Page rendering resolution | 300 DPI |
| Image colour mode | RGB |
| OCR method | Google Cloud Vision `document_text_detection()` |
| Low-confidence review threshold | 0.60 |
| Invisible PDF text rendering mode | 3 |
| PDF processing library | PyMuPDF |

These are the settings used during development. Adjust them in the scripts if your document requires different settings.

## Requirements

- Windows, macOS, or Linux
- Python 3.10 or newer recommended
- A Google Cloud project
- Cloud Vision API enabled
- Google Cloud authentication configured locally
- A scanned PDF that you are authorised to process

## Setup (Windows / PowerShell)

### 1. Clone the repository

```powershell
git clone https://github.com/sanjayvk926-hash/OCR.git
cd OCR
```

### 2. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:

```bat
venv\Scripts\activate.bat
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Google Cloud Vision

1. Create or select a Google Cloud project.
2. Enable the **Cloud Vision API**.
3. Configure billing if required by your Google Cloud account.
4. Install and configure the Google Cloud CLI.
5. Sign in and create Application Default Credentials:

```powershell
gcloud auth application-default login
gcloud config set project YOUR_GOOGLE_CLOUD_PROJECT_ID
```

Replace `YOUR_GOOGLE_CLOUD_PROJECT_ID` with your actual project ID.

The Python client uses Application Default Credentials. Do not commit access tokens, service-account keys, or credential files to GitHub.

### 5. Add your input PDF

Place your scanned PDF in the project directory. The main script was configured during development to read:

```text
tamil_document_1997.pdf
```

If your file has a different name or location, update the input path in `auto_searchable_pdf.py`.

### 6. Configure the Tamil font

The PDF text-layer script may require a Tamil-capable font file. The development environment used Nirmala UI extracted from Windows.

Make sure the font path configured in the script points to a valid font file on your computer. Font licensing may restrict redistribution, so do not upload extracted system fonts to this repository unless you have permission.

### 7. Run the pipeline

```powershell
python auto_searchable_pdf.py
```

The output filename configured during development is:

```text
tamil_document_searchable.pdf
```

The script may also create OCR JSON data and a low-confidence report under `ocr_data/`.

## Useful scripts

| Script | Purpose |
|---|---|
| `auto_searchable_pdf.py` | Main searchable-PDF workflow |
| `full_document_ocr.py` | Full-document OCR extraction |
| `preprocess.py` | Image preprocessing experiments |
| `extract_font.py` | Font extraction utility |

## Output and quality checks

After processing, verify:

- The output PDF has the expected number of pages.
- The scanned page appearance has not been unintentionally changed.
- Extracted text contains valid Tamil Unicode.
- Tamil words can be copied and pasted correctly.
- Ctrl+F can find known Tamil words.
- Invisible text aligns with the corresponding words in the scan.
- Low-confidence OCR results are reviewed manually.

You can inspect extracted text with PyMuPDF:

```python
import pymupdf

document = pymupdf.open("tamil_document_searchable.pdf")
print(document[0].get_text())
```

Readable text extraction alone does not prove that copy-and-paste, font mapping, or search works correctly in every PDF viewer. Test the output in more than one PDF reader.

## Important notes

- OCR is not guaranteed to be error-free. Handwriting, faded ink, stamps, tables, and damaged scans can reduce accuracy.
- Google Cloud Vision API usage may incur charges. Check current Google Cloud pricing and quotas before processing large batches.
- Keep original PDFs, generated PDFs, OCR data, credentials, and private documents out of public repositories unless you have permission to share them.
- Never commit Google Cloud credentials or access tokens.
- Treat the searchable PDF feature as experimental until Tamil copy/paste, search, and alignment have been verified.

## Repository

https://github.com/sanjayvk926-hash/OCR
