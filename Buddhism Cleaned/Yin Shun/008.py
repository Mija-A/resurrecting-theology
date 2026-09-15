"""
Extract body text from:
  008 An Explanation on the Uniqueness of the Law of Cause.pdf

Strips: footnotes, Chinese/CJK characters, superscript numbers, page numbers.
NOTE: starts on page 1 (no TOC page to skip).

Usage: update PDF_PATH and OUT_PATH below to match your local file locations.
"""

import re
import pdfplumber
from collections import defaultdict

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Yin Shun/008 An Explanation on the Uniqueness of the Law of Cause.pdf"
OUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Yin Shun/008 An Explanation on the Uniqueness of the Law of Cause_clean.txt"

CJK_RE = re.compile(r'[\u3000-\u9fff\uf900-\ufaff\ufe30-\ufe4f'
                    r'\u2e80-\u2eff\u31c0-\u31ef\u3200-\u32ff'
                    r'\u3400-\u4dbf\U00020000-\U0002a6df]+')


def find_footnote_cutoff(page):
    """
    Find where footnotes begin by looking for either:
    - A horizontal line object (rule) in the lower half of the page, OR
    - The first gap >= 50pt below 40% of page height.
    """
    # Check for a horizontal rule (footnote separator line)
    for obj in page.objects.get('rect', []):
        h = obj['height']
        y = obj['top']
        w = obj['width']
        # A thin wide horizontal line in the lower half of the page
        if h < 3 and w > 50 and y > page.height * 0.40:
            return y

    # Fall back to gap detection
    words = page.extract_words()
    if not words:
        return page.height
    y_vals = sorted(set(round(w['top']) for w in words))
    threshold = page.height * 0.40
    for i in range(1, len(y_vals)):
        if y_vals[i - 1] < threshold:
            continue
        if y_vals[i] - y_vals[i - 1] >= 50:
            return y_vals[i - 1]
    return page.height


def extract_body_text(page, cutoff_y):
    """
    Keep chars that are:
      - Font size >= 10.5pt (excludes 9.1pt footnotes and 7pt superscripts)
      - Above the footnote cutoff y
      - Not CJK characters
    """
    lines = defaultdict(list)
    for c in page.chars:
        if c['size'] < 10.5:
            continue
        if c['top'] > cutoff_y + 5:
            continue
        if CJK_RE.match(c['text']):
            continue
        lines[round(c['top'])].append(c)

    result = []
    for y in sorted(lines.keys()):
        chars = sorted(lines[y], key=lambda c: c['x0'])
        line_text = ''.join(c['text'] for c in chars).strip()
        if line_text:
            result.append(line_text)
    return result


def is_page_number(line, page_num):
    return line.strip().isdigit() and int(line.strip()) == page_num


def clean_text(lines):
    """Remove footnote ref digits after letters/punctuation, join hyphens, collapse spaces."""
    cleaned = []
    i = 0
    while i < len(lines):
        line = lines[i]
        line = re.sub(r'([a-zA-Z,\.\)\]])(\d{1,2})(\s)', r'\1\3', line)
        line = re.sub(r'([a-zA-Z,\.\)\]])(\d{1,2})$', r'\1', line)
        line = re.sub(r'  +', ' ', line).strip()
        if line.endswith('-') and i + 1 < len(lines):
            line = line[:-1] + lines[i + 1]
            i += 1
        if line:
            cleaned.append(line)
        i += 1
    return cleaned


def merge_into_paragraphs(lines):
    """
    Join lines into paragraphs. Section headings are detected as bold/large
    lines that are short and standalone. We keep it simple: just join all
    lines into flowing paragraphs separated by blank lines when a line
    looks like a standalone heading (short, no trailing punctuation).
    """
    paragraphs = []
    current = []
    for line in lines:
        # A heading: short line, doesn't end in punctuation mid-sentence,
        # and is not a continuation of a sentence
        is_heading = (
            len(line) < 100
            and not line.endswith(',')
            and not line.endswith(';')
            and re.match(r'^[A-Z\[]', line)
            and not re.search(r'\.$', line)  # headings don't end with period
            and len(line.split()) >= 3  # at least 3 words
        )
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
        # Start from page 1 (no TOC page to skip)
        for page_num, page in enumerate(pdf.pages, start=1):
            cutoff = find_footnote_cutoff(page)
            lines = extract_body_text(page, cutoff)
            lines = [l for l in lines if not is_page_number(l, page_num)]
            all_lines.extend(lines)

    # Secondary filter: remove footnote blocks starting with a number + capital letter
    footnote_start = re.compile(r'^\d{1,2}\s+[A-Z\u201c\u2018"]')
    filtered = []
    in_footnote = False
    for line in all_lines:
        if footnote_start.match(line):
            in_footnote = True
        elif in_footnote and len(line) > 80:
            in_footnote = False
        if not in_footnote:
            filtered.append(line)
    all_lines = filtered

    cleaned = clean_text(all_lines)
    paragraphs = merge_into_paragraphs(cleaned)

    output = '\n'.join(paragraphs)
    output = CJK_RE.sub('', output)
    output = re.sub(r'\(CBETA[^)]*\)', '', output)
    output = re.sub(r'\(\s*\)', '', output)
    output = re.sub(r'\n{3,}', '\n\n', output)

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write(output)

    print(f"Done. Written to {OUT_PATH}")
    print(f"Total characters: {len(output)}")


if __name__ == '__main__':
    main()