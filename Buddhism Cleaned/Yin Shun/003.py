"""
Extract body text from:
  003 Discourse on Practicing and Studying the Buddha-dharma.pdf

Strips: footnotes, Chinese/CJK characters, superscript numbers, page numbers, TOC (page 1).

Usage: update PDF_PATH and OUT_PATH below to match your local file locations.
"""

import re
import pdfplumber
from collections import defaultdict

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Yin Shun/003 Discourse on Practicing and Studying the Buddha-dharma.pdf"
OUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Yin Shun/003 Discourse on Practicing and Studying the Buddha-dharma_clean.txt"

CJK_RE = re.compile(r'[\u3000-\u9fff\uf900-\ufaff\ufe30-\ufe4f'
                    r'\u2e80-\u2eff\u31c0-\u31ef\u3200-\u32ff'
                    r'\u3400-\u4dbf\U00020000-\U0002a6df]+')


def find_footnote_cutoff(page):
    """
    Find where footnotes begin by looking for either:
    - A horizontal rule object (thin wide line) in the lower half of the page, OR
    - The first gap >= 50pt below 40% of page height.
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
        if y_vals[i] - y_vals[i - 1] >= 50:
            return y_vals[i - 1]
    return page.height


def extract_body_text(page, cutoff_y):
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
    paragraphs = []
    current = []
    for line in lines:
        is_heading = (
            len(line) < 100
            and not line.endswith(',')
            and not line.endswith(';')
            and re.match(r'^[A-Z\[]', line)
            and not re.search(r'\.$', line)
            and len(line.split()) >= 3
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
        # Skip page 1 (title + TOC), start from page 2
        for page_num, page in enumerate(pdf.pages[1:], start=2):
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