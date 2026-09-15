import fitz
import re
from collections import Counter

pdf_path = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Sri Aurobindo/KenaAndOtherUpanishads.pdf"
output_path = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Sri Aurobindo/KenaAndOtherUpanishads_clean.txt"

PAGE_OFFSET = 15

def is_page_number(s):
    return bool(re.fullmatch(r'\d+', s.strip()))

def is_section_marker(s):
    return bool(re.match(r'^\[.*\]$', s.strip()))

def is_chapter_label(s):
    if re.match(r'^(Chapter\s+)?[IVXLCDM]+$', s.strip(), re.IGNORECASE):
        return True
    if re.match(r'^(First|Second|Third|Fourth|Fifth)\s+Part$', s.strip(), re.IGNORECASE):
        return True
    return False

def has_unicode(s):
    non_ascii = sum(1 for c in s if ord(c) > 127)
    total = len(s.replace(" ", ""))
    if total == 0:
        return False
    return non_ascii / total > 0.3

def strip_garbled_words(s):
    # Remove inline garbled ASCII transliteration tokens (mid-word uppercase, all alpha)
    words = s.split()
    clean = []
    for w in words:
        # Skip short garbled tokens: all-alpha, has uppercase after first char
        if w.isalpha() and len(w) > 1 and any(c.isupper() for c in w[1:]):
            continue
        clean.append(w)
    return " ".join(clean).strip()

def is_empty_after_clean(s):
    return not strip_garbled_words(s).strip()

def clean_line(s):
    if has_unicode(s):
        return None
    cleaned = strip_garbled_words(s)
    if not cleaned:
        return None
    return cleaned

# Extract pages starting from PAGE_OFFSET
doc = fitz.open(pdf_path)
raw_pages = []
for i, page in enumerate(doc):
    if i < PAGE_OFFSET - 1:
        continue
    raw_pages.append(page.get_text("text").strip())

# Count repeating lines
line_counts = Counter()
for page_text in raw_pages:
    for line in page_text.split("\n"):
        s = line.strip()
        if s:
            line_counts[s] += 1

REPEAT_THRESHOLD = 3
repeating_lines = {line for line, count in line_counts.items() if count >= REPEAT_THRESHOLD}

# Collect all cleaned lines across pages
seen_repeated = set()
all_lines = []

for page_text in raw_pages:
    for line in page_text.split("\n"):
        s = line.strip()
        if not s:
            all_lines.append("")  # preserve intentional paragraph breaks
            continue
        if is_page_number(s):
            continue
        if is_section_marker(s):
            continue
        if is_chapter_label(s):
            continue
        if s in repeating_lines:
            if s in seen_repeated:
                continue
            else:
                seen_repeated.add(s)
        cleaned = clean_line(s)
        if cleaned:
            all_lines.append(cleaned)

# Merge hyphenated line breaks, rebuild paragraphs
paragraphs = []
current = []

i = 0
while i < len(all_lines):
    line = all_lines[i]
    if line == "":
        # Blank line = paragraph break
        if current:
            paragraphs.append(" ".join(current))
            current = []
    elif line.endswith("-") and i + 1 < len(all_lines) and all_lines[i+1] != "":
        # Hyphenated word split across lines — merge without space
        current.append(line[:-1] + all_lines[i+1])
        i += 2
        continue
    else:
        current.append(line)
    i += 1

if current:
    paragraphs.append(" ".join(current))

with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n\n".join(paragraphs))

print(f"Done! {len(paragraphs)} paragraphs written to {output_path}")
print(f"Started from PDF page {PAGE_OFFSET}, total pages processed: {len(raw_pages)}")