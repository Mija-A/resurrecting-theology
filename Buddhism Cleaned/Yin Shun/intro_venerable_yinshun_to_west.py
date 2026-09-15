import re
from pathlib import Path
import fitz  # pip install pymupdf

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Yin Shun/Introducing Venerable Yinshun to the West.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Yin Shun/Introducing_Yinshun_to_the_West_clean.txt"

START_PDF_PAGE = 18  # first content page

# Running headers that appear at top of alternating pages
HEADER_PATTERNS = [
    re.compile(r'^Chapter \d+$'),
    re.compile(r'^Introducing Venerable Yinshun', re.IGNORECASE),
    re.compile(r'^Outline of The Way to Buddhahood', re.IGNORECASE),
    re.compile(r'^The Pāramitā Practice', re.IGNORECASE),
    re.compile(r'^Bodhi Monastery', re.IGNORECASE),
]

def is_header_footer(s):
    for pat in HEADER_PATTERNS:
        if pat.match(s):
            return True
    return False

def is_junk(s):
    # standalone page numbers
    if re.fullmatch(r'\d+', s):
        return True
    # roman numerals
    if re.fullmatch(r'[ivxlIVXL]+', s):
        return True
    # running headers
    if is_header_footer(s):
        return True
    # low alpha content, short line (stray symbols, artifacts)
    alpha_ratio = sum(c.isalpha() for c in s) / max(len(s), 1)
    if alpha_ratio < 0.35 and len(s) < 60:
        return True
    return False

def clean_table_line(s):
    """Table cells use + as a word separator artifact — replace with spaces."""
    if '+' in s and re.search(r'\w\+\w', s):
        s = s.replace('+', ' ')
    return s

def clean_page(text):
    lines = text.split('\n')
    cleaned = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()

        if not s:
            i += 1
            continue

        if is_junk(s):
            i += 1
            continue

        # drop-cap artifact: single uppercase letter alone
        if re.match(r'^[A-Z]$', s) and i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            if nxt and nxt[0].islower():
                cleaned.append(s + nxt)
                i += 2
                continue

        # fix + artifacts from table cells
        s = clean_table_line(s)

        # bullet symbol artifacts (!, ✦, •, !, ★, etc.) — normalize to dash
        s = re.sub(r'^[!✦•★✓–]\s+', '- ', s)

        cleaned.append(s)
        i += 1

    result = '\n'.join(cleaned)
    # fix split drop-caps
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

    final = '\n\n'.join(blocks)
    Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(final)

    print(f"\nDone -> {len(blocks)} pages written to:\n  {OUTPUT_PATH}")

if __name__ == '__main__':
    main()