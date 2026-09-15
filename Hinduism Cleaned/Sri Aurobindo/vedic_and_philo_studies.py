import fitz
import re
from collections import Counter

pdf_path = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Sri Aurobindo/VedicAndPhilologicalStudies.pdf"
output_path = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Sri Aurobindo/VedicAndPhilologicalStudies_clean.txt"

PAGE_OFFSET = 19

def is_page_number(s):
    return bool(re.fullmatch(r'\d+', s.strip()))

def is_section_marker(s):
    return bool(re.match(r'^\[.*\]$', s.strip()))

def is_chapter_label(s):
    return bool(re.match(r'^(Chapter\s+)?[IVXLCDM]+$', s.strip(), re.IGNORECASE))

def has_unicode(s):
    return any(ord(c) > 127 for c in s)

def is_mostly_garbled(s):
    # Used for whole-line stripping — if the entire line is garbled
    words = s.split()
    if not words:
        return False
    garbled = sum(1 for w in words if len(w) > 1 and any(c.isupper() for c in w[1:]))
    return garbled / len(words) > 0.5

def strip_garbled_words(s):
    # Word-level stripping — remove garbled tokens but keep surrounding English
    words = s.split()
    clean = []
    for w in words:
        # Keep words that are normal English: uppercase only at start, or all punctuation/digits
        if len(w) > 1 and any(c.isupper() for c in w[1:]) and w.isalpha():
            continue  # garbled transliteration token, skip
        clean.append(w)
    return " ".join(clean).strip()

def clean_block(text):
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if is_page_number(s):
            continue
        if is_section_marker(s):
            continue
        if is_chapter_label(s):
            continue
        if has_unicode(s):
            continue
        if is_mostly_garbled(s):
            continue
        # For lines that are mostly English but contain some garbled words, clean inline
        s_clean = strip_garbled_words(s)
        if s_clean:
            cleaned.append(s_clean)
    return "\n".join(cleaned).strip()

# Extract pages starting from PAGE_OFFSET
doc = fitz.open(pdf_path)
raw_pages = []
for i, page in enumerate(doc):
    if i < PAGE_OFFSET - 1:
        continue
    raw_pages.append(page.get_text("text").strip())

# Count repeating lines across all pages
line_counts = Counter()
for page_text in raw_pages:
    for line in page_text.split("\n"):
        s = line.strip()
        if s:
            line_counts[s] += 1

REPEAT_THRESHOLD = 3
repeating_lines = {line for line, count in line_counts.items() if count >= REPEAT_THRESHOLD}

# Clean each page, keeping first occurrence of repeated lines
seen_repeated = set()

output_blocks = []
for page_text in raw_pages:
    cleaned = clean_block(page_text)
    if not cleaned:
        continue
    final_lines = []
    for line in cleaned.split("\n"):
        s = line.strip()
        if s in repeating_lines:
            if s in seen_repeated:
                continue
            else:
                seen_repeated.add(s)
        final_lines.append(line)
    final = "\n".join(final_lines).strip()
    if final:
        output_blocks.append(final)

with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n\n".join(output_blocks))

print(f"Done! {len(output_blocks)} non-empty pages written to {output_path}")
print(f"Started from PDF page {PAGE_OFFSET}, total pages processed: {len(raw_pages)}")