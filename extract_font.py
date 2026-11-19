
from fontTools.ttLib import TTCollection

font_collection = TTCollection(r"C:\Windows\Fonts\Nirmala.ttc")

print("Available fonts:", len(font_collection.fonts))

for index, font in enumerate(font_collection.fonts):
    output = f"Nirmala_{index}.ttf"
    font.flavor = None
    font.save(output)
    print(f"Extracted: {output}")
