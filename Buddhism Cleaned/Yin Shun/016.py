"""
Extract body text from Anandas_Faults.pdf, stripping:
  - Footnotes (identified by large vertical gap separating them from body)
  - Chinese/CJK characters
  - Superscript footnote reference numbers (size < 9pt)
  - Page numbers
"""

import re
import pdfplumber
from collections import defaultdict

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Yin Shun/016 Benefiting Others and Oneself.pdf"
OUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Yin Shun/016 Benefiting Others and Oneself_clean.txt"

# Regex to match any CJK / Chinese character
CJK_RE = re.compile(r'[\u3000-\u9fff\uf900-\ufaff\ufe30-\ufe4f'
                    r'\u2e80-\u2eff\u31c0-\u31ef\u3200-\u32ff'
                    r'\u3400-\u4dbf\U00020000-\U0002a6df]+')

# Also strip lone superscript-style numbers left over (e.g. "1941),5 I")
# These appear as isolated digits after punctuation
FOOTNOTE_REF_RE = re.compile(r'(?<=[^\s\d])(\d{1,2})(?=\s)')


def find_footnote_cutoff(page):
    """
    Find the y-coordinate where the footnote section begins.
    Looks for the largest vertical gap in text lines below y=400,
    which corresponds to the separator line between body and footnotes.
    Returns the y of the gap start, or page.height if no gap found.
    """
    words = page.extract_words()
    if not words:
        return page.height

    # Collect unique y-positions (rounded to avoid float noise)
    y_vals = sorted(set(round(w['top']) for w in words))

    # Only look for gaps in the lower half of the page
    mid = page.height * 0.5
    lower_y = [y for y in y_vals if y > mid]

    best_gap = 0
    cutoff = page.height

    for i in range(1, len(lower_y)):
        gap = lower_y[i] - lower_y[i - 1]
        if gap > best_gap:
            best_gap = gap
            cutoff = lower_y[i - 1]  # last body line before gap

    # Only treat it as a real footnote separator if gap is significant (>25pt)
    if best_gap < 25:
        return page.height

    return cutoff


def extract_body_text(page, cutoff_y):
    """
    Extract text from chars that are:
      - Above the footnote cutoff y
      - Font size >= 9pt (excludes superscript footnote numbers)
      - Not CJK characters
    Returns a list of text lines.
    """
    # Group chars into lines by rounded y-position
    lines = defaultdict(list)

    for c in page.chars:
        y = c['top']
        size = c['size']
        char = c['text']

        # Skip superscripts (footnote reference numbers in body)
        if size < 9.0:
            continue

        # Skip footnote region
        if y > cutoff_y + 5:  # small buffer
            continue

        # Skip CJK characters
        if CJK_RE.match(char):
            continue

        lines[round(y)].append(c)

    result = []
    for y in sorted(lines.keys()):
        chars = sorted(lines[y], key=lambda c: c['x0'])
        line_text = ''.join(c['text'] for c in chars).strip()
        if line_text:
            result.append(line_text)

    return result


def is_page_number(line, page_num):
    """Detect standalone page number lines."""
    stripped = line.strip()
    return stripped.isdigit() and int(stripped) == page_num


def clean_text(lines):
    """
    Post-process extracted lines:
    - Remove lines that are only page numbers
    - Remove residual footnote reference digits attached to words
    - Join hyphenated line-breaks
    - Normalise multiple spaces
    """
    cleaned = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Remove residual superscript footnote refs: digit(s) after a letter (not after a digit)
        # e.g. "community.4 " -> "community. "  but NOT "25 years" -> "2 years"
        line = re.sub(r'([a-zA-Z,\.\)\]])(\d{1,2})(\s)', r'\1\3', line)
        # Also at end of line: letter followed by lone digit(s)
        line = re.sub(r'([a-zA-Z,\.\)\]])(\d{1,2})$', r'\1', line)

        # Collapse multiple spaces
        line = re.sub(r'  +', ' ', line).strip()

        # Handle hyphenated word-break across lines
        if line.endswith('-') and i + 1 < len(lines):
            next_line = lines[i + 1]
            # Join and remove hyphen
            line = line[:-1] + next_line
            i += 1  # skip next line

        if line:
            cleaned.append(line)
        i += 1

    return cleaned


def merge_into_paragraphs(lines):
    """
    Re-join lines into paragraphs. A new paragraph starts when:
    - The line is a section heading (all caps or matches heading pattern)
    - There's a blank line
    We output a blank line between paragraphs.
    """
    paragraphs = []
    current = []

    HEADING_RE = re.compile(
        r'^(\d+\.|The Fault|Abbreviation|[A-Z][A-Z\s]+:?\s*$)'
    )

    for line in lines:
        is_heading = bool(HEADING_RE.match(line)) and len(line) < 100
        if is_heading:
            if current:
                paragraphs.append(' '.join(current))
                current = []
            paragraphs.append('')
            paragraphs.append(line)
        else:
            current.append(line)

    if current:
        paragraphs.append(' '.join(current))

    return paragraphs


def main():
    all_lines = []

    with pdfplumber.open(PDF_PATH) as pdf:
        # Skip page 1 (title/TOC) and last page (Abbreviations) — keep if desired
        for page_num, page in enumerate(pdf.pages, start=1):
            cutoff = find_footnote_cutoff(page)
            lines = extract_body_text(page, cutoff)

            # Filter out lone page number lines
            lines = [l for l in lines if not is_page_number(l, page_num)]

            all_lines.extend(lines)

    cleaned = clean_text(all_lines)
    paragraphs = merge_into_paragraphs(cleaned)

    output = '\n'.join(paragraphs)

    # Final pass: remove any stray CJK that slipped through
    output = CJK_RE.sub('', output)
    # Remove CBETA reference patterns entirely
    output = re.sub(r'\(CBETA[^)]*\)', '', output)
    # Remove standalone reference codes like "T22, no. 1421, p. 191b3"
    output = re.sub(r',?\s*[TN]\d+,\s*no\.\s*\d+[^)]*', '', output)
    # Clean up leftover empty parens
    output = re.sub(r'\(\s*\)', '', output)
    # Collapse multiple blank lines
    output = re.sub(r'\n{3,}', '\n\n', output)

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"Done. Written to {OUT_PATH}")
    print(f"Total characters: {len(output)}")


if __name__ == '__main__':
    main()