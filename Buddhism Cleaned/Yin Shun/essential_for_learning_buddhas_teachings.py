import re
from pathlib import Path
import fitz  # pip install pymupdf

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Yin Shun/The Three Essentials for Learning the Buddha\u2019s Teachings.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Yin Shun/The_Three_Essentials_clean.txt"

START_PDF_PAGE = 1  # 1-indexed

SKIP_LINES = {
    "the three essentials for learning the buddha's teachings",
    "three essentials for learning the buddha's teachings",
}

def is_junk(s):
    if re.fullmatch(r"\d+", s):
        return True
    if re.fullmatch(r"[ivxlIVXL]+", s):
        return True
    if s.lower() in SKIP_LINES:
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
    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    start_idx = START_PDF_PAGE - 1  # fitz is 0-indexed

    print(f"PDF has {total_pages} pages. Extracting from page {START_PDF_PAGE}...\n")

    blocks = []
    for page_num in range(start_idx, total_pages):
        page = doc[page_num]
        raw = page.get_text()
        cleaned = clean_page(raw)
        if cleaned:
            blocks.append(cleaned)
        print(f"  page {page_num + 1} done", flush=True)

    doc.close()

    final = "\n\n".join(blocks)
    Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(final)

    print(f"\nDone -> {len(blocks)} pages written to:\n  {OUTPUT_PATH}")

if __name__ == "__main__":
    main()