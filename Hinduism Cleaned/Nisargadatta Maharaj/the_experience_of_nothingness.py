import re
import unicodedata
import pytesseract
from pdf2image import convert_from_path

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Nisargadatta Maharaj/the experience of nothingness.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Nisargadatta Maharaj/The_Experience_of_Nothingness_cleaned.txt"

START_PAGE = 16
END_PAGE = 177

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

        # Skip standalone page numbers
        if re.fullmatch(r"\d+", s):
            continue

        # Skip running headers: chapter title followed by "- N"
        if re.search(r"\s+-\s+\d+$", s):
            continue

        # Skip known header strings
        if re.search(r"Experience of Nothingness", s, re.IGNORECASE):
            continue
        if re.search(r"Nisargadatta Maharaj", s, re.IGNORECASE):
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