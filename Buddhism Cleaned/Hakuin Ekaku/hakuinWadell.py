import re
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Hakuin Ekaku/HakuinWaddell.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Hakuin Ekaku/HakuinWaddell_clean.txt"

START_PDF_PAGE = 14
TOTAL_PDF_PAGES = 88

OCR_CONFIG = "--oem 1 --psm 6"

HEADER_PATTERNS = [
    re.compile(r'^\d+\s*[·•*]\s*.{0,60}$'),
    re.compile(r'^.{0,60}\s*[·•*]\s*\d+$'),
    re.compile(r'^\d+$'),
]

def is_header(line):
    s = line.strip()
    return any(p.match(s) for p in HEADER_PATTERNS)

def clean_half(text):
    lines = text.split("\n")
    cleaned = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()

        if not s or is_header(s):
            i += 1
            continue

        # drop-cap artifact: lone uppercase letter before lowercase continuation
        if re.match(r'^[A-Z]$', s) and i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            if nxt and nxt[0].islower():
                cleaned.append(s + nxt)
                i += 2
                continue

        cleaned.append(s)
        i += 1

    result = "\n".join(cleaned)
    # fix "P\nRECIOUS" style two-line all-caps splits
    result = re.sub(
        r'\n([A-Z])\n([A-Z]{2,})',
        lambda m: '\n' + m.group(1) + m.group(2),
        result,
    )
    return result.strip()

def main():
    print(f"Loading PDF pages {START_PDF_PAGE}–{TOTAL_PDF_PAGES} at 300 DPI…")

    images = convert_from_path(
        PDF_PATH,
        dpi=300,
        first_page=START_PDF_PAGE,
        last_page=TOTAL_PDF_PAGES,
        fmt="jpeg",
        thread_count=4,
    )

    print(f"  → {len(images)} page images ready. Starting OCR…\n")

    blocks = []
    for i, img in enumerate(images):
        pdf_page_num = START_PDF_PAGE + i
        w, h = img.size
        mid = w // 2

        left  = img.crop((0,   0, mid, h))
        right = img.crop((mid, 0, w,   h))

        for half in (left, right):
            raw = pytesseract.image_to_string(half, lang="eng", config=OCR_CONFIG)
            cleaned = clean_half(raw)
            if cleaned:
                blocks.append(cleaned)

        print(f"  PDF page {pdf_page_num}/{TOTAL_PDF_PAGES} done", flush=True)

    final = "\n\n".join(blocks)
    Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(final)

    print(f"\nDone — {len(blocks)} half-page blocks written to:\n  {OUTPUT_PATH}")

if __name__ == "__main__":
    main()