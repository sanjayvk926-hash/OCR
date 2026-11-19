
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

for i in range(6):
    filename = f"Nirmala_{i}.ttf"

    try:
        pdfmetrics.registerFont(TTFont(f"Tamil{i}", filename))
        print(f"SUCCESS: {filename}")
    except Exception as e:
        print(f"FAILED: {filename} - {e}")
