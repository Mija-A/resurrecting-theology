"""
yasenkanna_ocr.py
-----------------
Extracts the left-column text (Norman Waddell's translation) from
Yasenkanna2.pdf, which is laid out as a two-column comparison table
across pages 2–25.

The PDF has three columns:
  Col 0  (x=46–296)  : Waddell translation  ← we want this
  Col 1  (x=296–535) : Leggett translation
  Col 2  (x=535–572) : I Ching references

Strategy: use pdfplumber word-level extraction filtered by x-coordinate
to reliably pick up only the left column, reconstructing paragraph flow
from word positions. Then normalize and clean the result.

Requirements:
    pip install pdfplumber

Usage:
    python yasenkanna_ocr.py

Input:  Yasenkanna2.pdf   (in working directory)
Output: Yasenkanna_Waddell.txt
"""

import re
import pdfplumber

PDF_PATH    = "Yasenkanna2.pdf"
OUTPUT_PATH = "Yasenkanna_Waddell.txt"

# Pages to process (1-indexed). Page 1 is a cover page with no table.
START_PAGE = 2
END_PAGE   = 25  # inclusive

# Column boundaries (consistent across all pages)
LEFT_COL_X0  = 46.0
LEFT_COL_X1  = 296.0   # right edge of Waddell column
# Words starting beyond this x belong to Leggett or I Ching columns
COL_RIGHT_THRESHOLD = 296.0

# helpers

def words_in_left_col(page):
    """Return all words whose left edge is within the Waddell column."""
    words = page.extract_words(
        x_tolerance=3,
        y_tolerance=3,
        keep_blank_chars=False,
        use_text_flow=False,
    )
    return [w for w in words if w['x0'] < COL_RIGHT_THRESHOLD]


def group_words_into_lines(words, y_tolerance=3):
    """
    Group words that share approximately the same y-coordinate into lines,
    preserving reading order within each line.
    """
    if not words:
        return []
    # Sort by top y first, then x
    words = sorted(words, key=lambda w: (round(w['top'] / y_tolerance), w['x0']))
    lines = []
    current_line = [words[0]]
    current_y = words[0]['top']
    for w in words[1:]:
        if abs(w['top'] - current_y) <= y_tolerance:
            current_line.append(w)
        else:
            lines.append(current_line)
            current_line = [w]
            current_y = w['top']
    if current_line:
        lines.append(current_line)
    return lines


def lines_to_paragraphs(lines, line_gap_threshold=6):
    """
    Join words in each line into strings, then merge lines into paragraphs
    based on vertical gap between lines. A larger-than-normal gap signals
    a new paragraph.
    """
    if not lines:
        return []

    # Compute average line height from the data
    line_tops = [l[0]['top'] for l in lines]
    gaps = [line_tops[i+1] - line_tops[i] for i in range(len(line_tops)-1)]
    avg_gap = (sum(gaps) / len(gaps)) if gaps else 12

    # Render each line to a string
    rendered = []
    for line in lines:
        rendered.append(' '.join(w['text'] for w in line))

    # Merge into paragraphs: new paragraph when gap > avg * threshold factor
    paragraphs = []
    current = [rendered[0]]
    for i, text in enumerate(rendered[1:], start=1):
        gap = line_tops[i] - line_tops[i-1]
        if gap > avg_gap * 1.6:
            # New paragraph
            paragraphs.append(' '.join(current))
            current = [text]
        else:
            current.append(text)
    if current:
        paragraphs.append(' '.join(current))

    return paragraphs


# main extraction

def extract_waddell(pdf_path, start_page, end_page):
    """Extract and return Waddell's left-column text as a list of paragraphs."""
    all_paragraphs = []

    with pdfplumber.open(pdf_path) as pdf:
        total = len(pdf.pages)
        for page_num in range(start_page - 1, min(end_page, total)):
            page = pdf.pages[page_num]
            words = words_in_left_col(page)
            if not words:
                continue
            lines = group_words_into_lines(words, y_tolerance=3)
            paragraphs = lines_to_paragraphs(lines)
            all_paragraphs.extend(paragraphs)

    return all_paragraphs


# cleaning

# Footer pattern present on every page
FOOTER_PATTERN = re.compile(
    r"Master Hakuin's Yasen Kanna\s*[–-]\s*2 translations compiled.*?Page\s*\d+",
    re.IGNORECASE
)

# Section headers that appear in the left column (keep these)
SECTION_HEADERS = {
    "MASTER HAKUYŪ", "CURE", "SUSTAINING LIFE",
    "REMEDIES POR SUSTAINING LIFE AND ACHIEVING IMMORTALITY",
    "REMEDIES FOR SUSTAINING LIFE AND ACHIEVING IMMORTALITY",
    "DRAWING THE MIND INTO THE LOWER BODY",
    "NON-CONTEMPLATION", "THE SOFT BUTTER METHOD",
    "CULTIVATING THE MIND ENERGY", "TAKING LEAVE OF HAKUYU",
    "THE BENEFITS OF INTROSPECTIVE MEDITATION", "EPILOGUE",
}


def clean_paragraph(p):
    """Clean a single paragraph string."""
    # Remove footer lines
    p = FOOTER_PATTERN.sub('', p).strip()

    # Normalize whitespace
    p = re.sub(r'\s+', ' ', p).strip()

    # Remove standalone page-number artifacts like "Page 2" at start/end
    p = re.sub(r'^Page\s+\d+\s*', '', p)
    p = re.sub(r'\s*Page\s+\d+$', '', p)

    # Remove the column header row that appears at the top of page 2
    if re.match(r"Norman Waddell'?s? translation", p, re.IGNORECASE):
        return ''
    if re.match(r"Trevor Legett'?s? translation", p, re.IGNORECASE):
        return ''
    if re.match(r"Master HAKUIN'?s? YASEN KANNA", p, re.IGNORECASE):
        return ''

    # Fix common hyphenation artifacts (word broken across lines)
    p = re.sub(r'(\w)-\s+(\w)', r'\1\2', p)

    # Fix "y everyday" -> "my everyday" (OCR quirk on page 3)
    p = p.replace(' y everyday', ' my everyday')

    # Remove I Ching reference tokens that bled in (e.g. "I Ching ref." or "Hex #24")
    p = re.sub(r'\bI\s+Ching\s+ref\.?\b', '', p)
    p = re.sub(r'\bHex\s*#?\d+\b', '', p)

    # Fix smart quotes to straight
    p = p.replace('\u2018', "'").replace('\u2019', "'")
    p = p.replace('\u201c', '"').replace('\u201d', '"')
    p = p.replace('\u2014', '--').replace('\u2013', '-')

    # Remove stray bullet/symbol characters
    p = re.sub(r'[•·‧▪■]', '', p)

    # Collapse any double spaces left over
    p = re.sub(r'  +', ' ', p).strip()

    return p


def is_junk(p):
    """Return True if this paragraph should be discarded entirely."""
    if not p:
        return True
    # Very short lines that are just noise
    if len(p) < 3:
        return True
    # I Ching ref column bleed-through
    if re.match(r'^(I\s+Ching|ref\.|Hex\s*#?\d+)$', p.strip(), re.IGNORECASE):
        return True
    # Footer artifact
    if 'Frederic Lecut' in p:
        return True
    # "Page N" standing alone
    if re.match(r'^Page\s+\d+$', p.strip()):
        return True
    return False


def clean_all(paragraphs):
    cleaned = []
    for p in paragraphs:
        p = clean_paragraph(p)
        if not is_junk(p):
            cleaned.append(p)
    return cleaned


# merge consecutive short lines that belong together

def merge_fragments(paragraphs):
    """
    The word-grouping sometimes produces over-split paragraphs when the
    inter-line gap varies. This pass merges a line into the previous one
    if it doesn't look like a new sentence/paragraph start and the previous
    line is also short (likely a fragment).
    """
    if not paragraphs:
        return paragraphs

    result = [paragraphs[0]]
    for p in paragraphs[1:]:
        prev = result[-1]
        # If prev ends mid-sentence (no terminal punctuation) and current
        # starts with lowercase, merge them
        prev_ends_open = prev and not re.search(r'[.!?\"\']$', prev.rstrip())
        curr_starts_lower = p and p[0].islower()
        is_header = p.upper() == p and len(p) > 4  # all-caps = section header

        if not is_header and prev_ends_open and curr_starts_lower:
            result[-1] = prev + ' ' + p
        else:
            result.append(p)
    return result


# main

def main():
    print(f"Extracting left column from {PDF_PATH} (pages {START_PAGE}–{END_PAGE})...")
    paragraphs = extract_waddell(PDF_PATH, START_PAGE, END_PAGE)

    print(f"  Raw paragraphs extracted: {len(paragraphs)}")
    paragraphs = clean_all(paragraphs)
    print(f"  After cleaning: {len(paragraphs)}")
    paragraphs = merge_fragments(paragraphs)
    print(f"  After merging fragments: {len(paragraphs)}")

    output = '\n\n'.join(paragraphs).strip()

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"\nDone. Written to: {OUTPUT_PATH}")
    print(f"Total characters: {len(output):,}")
    print(f"Total words:      {len(output.split()):,}")


if __name__ == '__main__':
    main()