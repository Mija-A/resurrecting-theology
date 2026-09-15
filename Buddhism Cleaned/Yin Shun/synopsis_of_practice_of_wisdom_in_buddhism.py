import re
from pathlib import Path
import fitz  # pip install pymupdf

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Yin Shun/Synopsis on the Practice of Wisdom in Buddhism (Part 1).pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Yin Shun/Synopsis_Wisdom_Part1_clean.txt"

START_PDF_PAGE = 2  # skip cover/TOC page

SKIP_LINES = {
    "synopsis on the practice of wisdom in buddhism",
    "synopsis on the practice of wisdom in buddhism (part 1)",
    "(part 1)",
}

def is_junk(s):
    # standalone page numbers
    if re.fullmatch(r"\d+", s):
        return True
    # roman numerals alone
    if re.fullmatch(r"[ivxlIVXL]+", s):
        return True
    # known header/footer lines
    if s.lower() in SKIP_LINES:
        return True
    # low alpha-ratio short lines (e.g. stray symbols, page artifacts)
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

        # footnote section separator
        if re.fullmatch(r"[_\-─—]{3,}", s):
            in_footnote = True
            i += 1
            continue

        if in_footnote:
            i += 1
            continue

        # numbered footnote starter like "1." or "1. 2."
        if re.fullmatch(r"(\d{1,2}\.\s*)+", s):
            in_footnote = True
            i += 1
            continue

        # drop-cap artifact: single uppercase letter on its own line
        if re.match(r'^[A-Z]$', s) and i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            if nxt and nxt[0].islower():
                cleaned.append(s + nxt)
                i += 2
                continue

        # dangling list marker e.g. "1." or "iv."
        if re.fullmatch(r"([\divxlIVXL]+)\.", s) and i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            if nxt:
                cleaned.append(s + " " + nxt)
                i += 2
                continue

        cleaned.append(s)
        i += 1

    result = "\n".join(cleaned)
    # fix split drop-caps across lines
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