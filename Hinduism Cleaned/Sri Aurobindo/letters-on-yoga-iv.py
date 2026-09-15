import fitz
import re
from collections import Counter

pdf_path = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Sri Aurobindo/letters-on-yoga-iv.pdf"
output_path = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Sri Aurobindo/letters-on-yoga-iv_clean.txt"

PAGE_OFFSET = 29

def is_page_number(s):
    return bool(re.fullmatch(r'\d+', s.strip()))

def has_unicode(s):
    non_ascii = sum(1 for c in s if ord(c) > 127)
    total = len(s.replace(" ", ""))
    if total == 0:
        return False
    return non_ascii / total > 0.3

def is_garbled_transliteration(s):
    words = s.split()
    if not words:
        return False
    garbled = sum(1 for w in words if w.isalpha() and len(w) > 1 and any(c.isupper() for c in w[1:]))
    return garbled / len(words) > 0.5

# Extract pages starting from PAGE_OFFSET
doc = fitz.open(pdf_path)
raw_pages = []
for i, page in enumerate(doc):
    if i < PAGE_OFFSET - 1:
        continue
    raw_pages.append(page.get_text("text").strip())

print(f"Total pages in PDF: {len(doc)}")
print(f"Pages extracted (from page {PAGE_OFFSET}): {len(raw_pages)}")

# Detect repeating headers/footers
line_counts = Counter()
for page_text in raw_pages:
    for line in page_text.split("\n"):
        s = line.strip()
        if s:
            line_counts[s] += 1

REPEAT_THRESHOLD = max(20, len(raw_pages) // 10)
MAX_HEADER_WORDS = 6

repeating_lines = {
    line for line, count in line_counts.items()
    if count >= REPEAT_THRESHOLD and len(line.split()) <= MAX_HEADER_WORDS
}

print(f"Threshold used: {REPEAT_THRESHOLD}")
print(f"Repeating lines detected: {len(repeating_lines)}")
for line in sorted(repeating_lines):
    print(f"  '{line}'")

# Collect and clean all lines, preserving structure
seen_repeated = set()
output_lines = []

for page_text in raw_pages:
    for line in page_text.split("\n"):
        s = line.strip()
        if not s:
            output_lines.append("")
            continue
        if is_page_number(s):
            continue
        if has_unicode(s):
            continue
        if is_garbled_transliteration(s):
            continue
        if s in repeating_lines:
            if s in seen_repeated:
                continue
            else:
                seen_repeated.add(s)
        output_lines.append(s)

# Collapse excessive consecutive blank lines
cleaned = []
prev_blank = False
for line in output_lines:
    if line == "":
        if not prev_blank:
            cleaned.append("")
        prev_blank = True
    else:
        cleaned.append(line)
        prev_blank = False

with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(cleaned))

print(f"Done! {len(cleaned)} lines written to {output_path}")