import fitz
import re
from collections import Counter

pdf_path = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Sri Aurobindo/IshaUpanishad.pdf"
output_path = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Sri Aurobindo/IshaUpanishad_clean.txt"

PAGE_OFFSET = 15

def is_page_number(s):
    return bool(re.fullmatch(r'\d+', s.strip()))

def is_section_marker(s):
    return bool(re.match(r'^\[.*\]$', s.strip()))

def is_chapter_label(s):
    return bool(re.match(r'^(Chapter\s+)?[IVXLCDM]+$', s.strip(), re.IGNORECASE))

def has_unicode(s):
    # Strip lines that are purely or predominantly Devanagari/unicode
    non_ascii = sum(1 for c in s if ord(c) > 127)
    total = len(s.replace(" ", ""))
    if total == 0:
        return False
    # If more than 30% of characters are unicode, strip the line
    return non_ascii / total > 0.3

# ── Step 1: Extract pages starting from PAGE_OFFSET ───────────────────────
doc = fitz.open(pdf_path)
raw_pages = []
for i, page in enumerate(doc):
    if i < PAGE_OFFSET - 1:
        continue
    raw_pages.append(page.get_text("text").strip())

# ── Step 2: Count repeating lines across all pages ────────────────────────
line_counts = Counter()
for page_text in raw_pages:
    for line in page_text.split("\n"):
        s = line.strip()
        if s:
            line_counts[s] += 1

REPEAT_THRESHOLD = 3
repeating_lines = {line for line, count in line_counts.items() if count >= REPEAT_THRESHOLD}

# ── Step 3: Clean each page ───────────────────────────────────────────────
seen_repeated = set()

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
        cleaned.append(line.rstrip())
    return "\n".join(cleaned).strip()

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