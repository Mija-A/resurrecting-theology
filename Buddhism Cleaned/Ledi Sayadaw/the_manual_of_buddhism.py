import re
import sys
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Ledi Sayadaw/Ledi-Sayadaw-The-Manual-of-Buddhism.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Ledi Sayadaw/Ledi-Sayadaw-The-Manual-of-Buddhism_clean.txt"

START_PDF_PAGE = 25

OCR_CONFIG = "--oem 1 --psm 6"

def is_footnote_trigger(line):
    s = line.strip()
    if re.fullmatch(r"[_\-─—]{3,}", s):
        return True
    # footnote number clusters: "4." or "4. 5." etc.
    if re.fullmatch(r"(\d{1,2}\.\s*)+", s):
        return True
    return False

def clean_page(text):
    lines = text.split("\n")
    cleaned = []
    in_footnote = False
    i = 0
    while i < len(lines):
        s = lines[i].strip()

        if not s:
            i += 1
            continue

        if re.fullmatch(r"\d+", s):
            i += 1
            continue

        if re.fullmatch(r"[ivxlIVXL]+", s):
            i += 1
            continue

        if is_footnote_trigger(lines[i]):
            in_footnote = True
            i += 1
            continue

        if in_footnote:
            i += 1
            continue

        # drop-cap artifact
        if re.match(r'^[A-Z]$', s) and i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            if nxt and nxt[0].islower():
                cleaned.append(s + nxt)
                i += 2
                continue

        # merge dangling list markers
        if re.fullmatch(r"([\divxlIVXL]+)\.", s) and i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            if nxt:
                cleaned.append(s + " " + nxt)
                i += 2
                continue

        cleaned.append(s)
        i += 1

    result = "\n".join(cleaned)
    result = re.sub(
        r'\n([A-Z])\n([A-Z]{2,})',
        lambda m: '\n' + m.group(1) + m.group(2),
        result,
    )
    return result.strip()

def main():
    print(f"Loading PDF from page {START_PDF_PAGE} at 300 DPI...")

    images = convert_from_path(
        PDF_PATH,
        dpi=300,
        first_page=START_PDF_PAGE,
        fmt="jpeg",
        thread_count=4,
    )

    print(f"  -> {len(images)} pages ready. Starting OCR...\n")

    blocks = []
    for i, img in enumerate(images):
        pdf_page_num = START_PDF_PAGE + i
        raw = pytesseract.image_to_string(img, lang="eng", config=OCR_CONFIG)
        cleaned = clean_page(raw)
        if cleaned:
            blocks.append(cleaned)
        print(f"  page {pdf_page_num} done", flush=True)

    final = "\n\n".join(blocks)
    Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(final)

    print(f"\nDone -> {len(blocks)} pages written to:\n  {OUTPUT_PATH}")

if __name__ == "__main__":
    main()