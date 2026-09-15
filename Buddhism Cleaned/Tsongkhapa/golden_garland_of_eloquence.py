import re
from pathlib import Path
from pdf2image import convert_from_path
import pytesseract

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Tsongkhapa/golden-garland-of-eloquence-legs-bshad-gser-phreng-volume-one-first-abhisamaya.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Tsongkhapa/golden-garland-of-eloquence-legs-bshad-gser-phreng-volume-one-first-abhisamaya_clean.txt"

START_PDF_PAGE = 30

OCR_CONFIG = "--oem 1 --psm 6"

SKIP_LINES = {
    "golden garland of eloquence",
}

def is_junk(s):
    if re.fullmatch(r"\d+", s):
        return True
    if re.fullmatch(r"[ivxlIVXL]+", s):
        return True
    if s.lower() in SKIP_LINES:
        return True
    # catch "Legs bshad gser phreng" with any trailing number or text
    if re.match(r'^legs bshad gser phreng', s, re.IGNORECASE):
        return True
    alpha_ratio = sum(c.isalpha() for c in s) / max(len(s), 1)
    if alpha_ratio < 0.4 and len(s) < 60:
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

        if is_junk(s):
            i += 1
            continue

        if re.fullmatch(r"[_\-─—]{3,}", s):
            in_footnote = True
            i += 1
            continue

        if in_footnote:
            i += 1
            continue

        if re.fullmatch(r"(\d{1,2}\.\s*)+", s):
            in_footnote = True
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