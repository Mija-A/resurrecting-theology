"""
Extract body text from:
  002 Attaining No Physical Suffering from No Psychological Suffering
  A Speech Given at the Losheng Sanatorium.pdf

Strips: footnotes, Chinese/CJK characters, superscript numbers, page numbers,
        running headers, TOC lines.
Preserves: Introduction paragraph and all body content from page 1 onward.

Usage: update PDF_PATH and OUT_PATH below to match your local file locations.
"""

import re
import pdfplumber
from collections import defaultdict

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Yin Shun/002 Attaining No Physical Suffering from No Psychological Suffering  A Speech Given at the Losheng Sanatorium.pdf"
OUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Yin Shun/002 Attaining No Physical Suffering from No Psychological Suffering_clean.txt"

CJK_RE = re.compile(r'[\u3000-\u9fff\uf900-\ufaff\ufe30-\ufe4f'
                    r'\u2e80-\u2eff\u31c0-\u31ef\u3200-\u32ff'
                    r'\u3400-\u4dbf\U00020000-\U0002a6df]+')

# TOC lines: all-caps or bold heading text followed by a page number
TOC_LINE_RE = re.compile(r'^[A-Z][A-Z\s,\-\']+\s+\d+$')

# Known front-matter lines to skip entirely
SKIP_LINES = {
    'contents',
    'extract from the buddha-dharma is the light to save the world',
    'author: venerable yinshun',
    'source text: no.002',
    'translated by yinshun cultural & educational foundation translation',
    'team',
    'the way to be free from suffering',
}


def find_footnote_cutoff(page):
    """
    Find where footnotes begin: horizontal rule OR gap >= 80pt below 40% of page.
    Using 80pt (not 50pt) so that the large TOC spacing on page 1 is not
    mistaken for a footnote separator.
    """
    for obj in page.objects.get('rect', []):
        if obj['height'] < 3 and obj['width'] > 50 and obj['top'] > page.height * 0.40:
            return obj['top']

    words = page.extract_words()
    if not words:
        return page.height
    y_vals = sorted(set(round(w['top']) for w in words))
    threshold = page.height * 0.40
    for i in range(1, len(y_vals)):
        if y_vals[i - 1] < threshold:
            continue
        if y_vals[i] - y_vals[i - 1] >= 80:
            return y_vals[i - 1]
    return page.height


def extract_body_text(page, cutoff_y):
    """
    Keep chars >= 10.5pt, below header zone, above footnote cutoff, not CJK.
    """
    HEADER_ZONE = 50  # top ~50pt contains running headers on later pages

    lines = defaultdict(list)
    for c in page.chars:
        if c['size'] < 10.5:
            continue
        if c['top'] < HEADER_ZONE:
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
        if not line_text:
            continue
        if line_text.lower() in SKIP_LINES:
            continue
        if TOC_LINE_RE.match(line_text):
            continue
        # Skip standalone page numbers
        if re.match(r'^\d+$', line_text):
            continue
        result.append(line_text)
    return result


def clean_text(lines):
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
    Join wrapped lines into paragraphs. Headings are short lines with no
    trailing period, comma, or semicolon, and contain no numbers.
    """
    paragraphs = []
    current = []

    for line in lines:
        is_heading = (
            len(line) < 80
            and re.match(r'^[A-Z]', line)
            and not re.search(r'[,;\.]$', line)
            and not re.search(r'\d', line)
            and len(line.split()) <= 10
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
        for page_num, page in enumerate(pdf.pages, start=1):
            cutoff = find_footnote_cutoff(page)
            lines = extract_body_text(page, cutoff)
            all_lines.extend(lines)

    # Secondary filter: remove footnote blocks starting with number + capital
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