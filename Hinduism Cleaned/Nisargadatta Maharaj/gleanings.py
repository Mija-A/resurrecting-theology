import re
import os
import subprocess
import tempfile
import unicodedata
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Nisargadatta Maharaj/Gleanings.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Nisargadatta Maharaj/Gleanings_cleaned.txt"

START_PAGE = 9
END_PAGE = 133

def ocr_page(pdf_path, page_num):
    imgs = convert_from_path(pdf_path, dpi=200, first_page=page_num, last_page=page_num)
    return pytesseract.image_to_string(imgs[0])

def strip_diacritics(text):
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")

def clean_page(ocr_text):
    lines = ocr_text.split("\n")
    cleaned = []
    for line in lines:
        s = line.strip()
        # Skip standalone page numbers
        if re.fullmatch(r"\d+", s):
            continue
        cleaned.append(strip_diacritics(line.rstrip()))

    # Collapse 3+ blank lines to 2
    text = "\n".join(cleaned)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text

print(f"Processing pages {START_PAGE}-{END_PAGE}...")
output_blocks = []

for page_num in range(START_PAGE, END_PAGE + 1):
    if page_num % 20 == 0:
        print(f"  Page {page_num}...")
    try:
        raw = ocr_page(PDF_PATH, page_num)
        cleaned = clean_page(raw)
        if cleaned:
            output_blocks.append(cleaned)
    except Exception as e:
        print(f"  Warning: page {page_num} failed: {e}")

final = "\n\n".join(output_blocks)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(final)

print(f"\nDone! {len(output_blocks)} pages written to:\n{OUTPUT_PATH}")