import re
import unicodedata
import pytesseract
from pdf2image import convert_from_path

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Nisargadatta Maharaj/the Nectar of Immortality.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Nisargadatta Maharaj/The_Nectar_of_Immortality_cleaned.txt"

START_PAGE = 14
END_PAGE = 107

def ocr_page(pdf_path, page_num):
    imgs = convert_from_path(pdf_path, dpi=200, first_page=page_num, last_page=page_num)
    return pytesseract.image_to_string(imgs[0])

def strip_diacritics(text):
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")

def clean_page(ocr_text):
    lines = ocr_text.split("\n")
    cleaned = []
    in_footnote = False

    for line in lines:
        s = line.strip()

        if not s:
            cleaned.append("")
            in_footnote = False
            continue

        # Skip standalone page numbers and roman numerals
        if re.fullmatch(r"\d+", s):
            continue
        if re.fullmatch(r"[ivxlcdmIVXLCDM]+", s):
            continue

        # Skip running headers
        if re.search(r"Nectar of Immortality", s, re.IGNORECASE):
            continue
        if re.search(r"Nisargadatta", s, re.IGNORECASE):
            continue
        if re.match(r"^[ivxlcdmIVXLCDM\d]+\s*[-·.]\s*", s):
            continue
        if re.search(r"\s*[-·.]\s*[ivxlcdmIVXLCDM\d]+$", s):
            continue

        # Skip photo captions
        if re.search(r"[Pp]hoto\s+by|courtesy of|1897|1981", s):
            continue

        # Detect footnote block
        if re.match(r"^\d+\s+[A-Z]", s):
            in_footnote = True
        if in_footnote:
            continue

        # Remove inline footnote markers
        line = re.sub(r"(?<=\w)\d+(?=\s|$)", "", line)
        cleaned.append(strip_diacritics(line.rstrip()))

    text = "\n".join(cleaned)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text

print(f"Processing pages {START_PAGE}-{END_PAGE}...")
output_blocks = []

for page_num in range(START_PAGE, END_PAGE + 1):
    if page_num % 10 == 0:
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