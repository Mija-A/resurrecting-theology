import re
from pathlib import Path
import fitz

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Yin Shun/006 Confidence and Its Cultivation.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Yin Shun/006_Confidence_and_Its_Cultivation_clean.txt"

START_PDF_PAGE = 2

SKIP_LINES = {
    "confidence and its cultivation",
}

# Footnote block opener: line starts with a digit (1-2) followed by space, Chinese char, or «
FOOTNOTE_BLOCK_RE = re.compile(r'^\d{1,2}[\s\u300a\u300b《》「」（）]')

# Inline superscript footnote markers: word immediately followed by digit(s) e.g. "confidence.7"
INLINE_FOOTNOTE_RE = re.compile(r'(\w)(\d{1,2})(\s)')

def is_english(s):
    """Return True if line is predominantly ASCII/Latin text worth keeping."""
    if not s:
        return False
    # count characters that are basic latin, extended latin, punctuation, digits
    latin = sum(1 for c in s if ord(c) < 0x0600)
    return latin / len(s) > 0.7

def is_junk(s):
    if re.fullmatch(r'\d+', s):
        return True
    if re.fullmatch(r'[ivxlIVXL]+', s):
        return True
    if s.lower() in SKIP_LINES:
        return True
    alpha_ratio = sum(c.isalpha() for c in s) / max(len(s), 1)
    if alpha_ratio < 0.4 and len(s) < 60:
        return True
    return False

def clean_page(text):
    lines = text.split('\n')
    cleaned = []
    in_footnote = False
    i = 0
    while i < len(lines):
        s = lines[i].strip()

        if not s:
            i += 1
            continue

        # footnote block separator line
        if re.fullmatch(r'[_\-─—]{3,}', s):
            in_footnote = True
            i += 1
            continue

        # footnote block opener: digit + space/Chinese
        if FOOTNOTE_BLOCK_RE.match(s):
            in_footnote = True
            i += 1
            continue

        if in_footnote:
            # exit footnote mode only for clear English body text:
            # long line, starts with capital letter, no leading digit
            if len(s) > 50 and s[0].isupper() and not re.match(r'^\d', s) and is_english(s):
                in_footnote = False
            else:
                i += 1
                continue

        if is_junk(s):
            i += 1
            continue

        # skip non-English lines (Chinese source text etc.)
        if not is_english(s):
            i += 1
            continue

        # strip inline superscript footnote markers e.g. "confidence.7 For" -> "confidence. For"
        s = INLINE_FOOTNOTE_RE.sub(lambda m: m.group(1) + m.group(3), s)

        # drop-cap artifact
        if re.match(r'^[A-Z]$', s) and i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            if nxt and nxt[0].islower():
                cleaned.append(s + nxt)
                i += 2
                continue

        # dangling list markers
        if re.fullmatch(r'([\divxlIVXL]+)\.', s) and i + 1 < len(lines):
            nxt = lines[i + 1].strip()
            if nxt:
                cleaned.append(s + ' ' + nxt)
                i += 2
                continue

        cleaned.append(s)
        i += 1

    result = '\n'.join(cleaned)
    result = re.sub(
        r'\n([A-Z])\n([A-Z]{2,})',
        lambda m: '\n' + m.group(1) + m.group(2),
        result,
    )
    return result.strip()

def main():
    doc = fitz.open(PDF_PATH)
    total_pages = len(doc)
    start_idx = START_PDF_PAGE - 1

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