import fitz
import re
from collections import Counter

pdf_path = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Sri Aurobindo/Savitri.pdf"
output_path = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Sri Aurobindo/Savitri_clean.txt"

PAGE_OFFSET = 23

def is_page_number(s):
    return bool(re.fullmatch(r'\d+', s.strip()))

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

# Collect all lines, merging hyphenated breaks
seen_repeated = set()
all_lines = []

for page_text in raw_pages:
    for line in page_text.split("\n"):
        s = line.strip()
        if not s:
            continue  # skip blank lines entirely
        if is_page_number(s):
            continue
        if s in repeating_lines:
            if s in seen_repeated:
                continue
            else:
                seen_repeated.add(s)
        all_lines.append(s)

# Merge hyphenated word splits
merged_lines = []
i = 0
while i < len(all_lines):
    line = all_lines[i]
    if line.endswith("-") and i + 1 < len(all_lines):
        merged_lines.append(line[:-1] + all_lines[i + 1])
        i += 2
    else:
        merged_lines.append(line)
        i += 1

# Join all lines into continuous prose
full_text = " ".join(merged_lines)

with open(output_path, "w", encoding="utf-8") as f:
    f.write(full_text)

print(f"Done! {len(merged_lines)} lines written as continuous prose")
print(f"Total characters: {len(full_text)}")