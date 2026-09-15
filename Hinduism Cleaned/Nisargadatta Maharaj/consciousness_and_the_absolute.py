import re
import os
import subprocess
import pytesseract
from PIL import Image

Image.MAX_IMAGE_PIXELS = None  # disable decompression bomb check

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Nisargadatta Maharaj/consciousness and the absolute.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Nisargadatta Maharaj/Consciousness_and_the_Absolute_cleaned.txt"

START_PAGE = 4
END_PAGE = 67

def ocr_page(page_num):
    prefix = "/tmp/ocr_page"
    subprocess.run([
        "pdftoppm", "-jpeg", "-r", "200",  # lowered from 300 to 200 DPI
        "-f", str(page_num), "-l", str(page_num),
        PDF_PATH, prefix
    ], check=True, capture_output=True)
    files = sorted([f for f in os.listdir("/tmp") if f.startswith("ocr_page") and f.endswith(".jpg")])
    if not files:
        return ""
    img_path = f"/tmp/{files[-1]}"
    text = pytesseract.image_to_string(Image.open(img_path), lang='eng')
    os.remove(img_path)
    return text

def clean_page(text):
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        s = line.strip()
        if not s:
            cleaned.append("")
            continue
        if re.fullmatch(r"\d+", s):
            continue
        if re.fullmatch(r"[ivxlcdmIVXLCDM]+", s):
            continue
        if re.search(r"Consciousness and the Absolute", s, re.IGNORECASE):
            continue
        if re.search(r"Talks of Nisargadatta Maharaj", s, re.IGNORECASE):
            continue
        if re.match(r"^\d+\s*/\s*", s) or re.search(r"\s*/\s*\d+$", s):
            continue
        cleaned.append(line)
    text = "\n".join(cleaned)
    return re.sub(r"\n{3,}", "\n\n", text).strip()

print(f"Starting OCR on pages {START_PAGE}–{END_PAGE}...")
all_text = []

for page_num in range(START_PAGE, END_PAGE + 1):
    print(f"  Processing page {page_num}/{END_PAGE}...", end="\r")
    raw = ocr_page(page_num)
    cleaned = clean_page(raw)
    if cleaned:
        all_text.append(cleaned)

output = "\n\n".join(all_text)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(output)

print(f"\nDone! Written to:\n{OUTPUT_PATH}")
print(f"Total characters: {len(output):,}")