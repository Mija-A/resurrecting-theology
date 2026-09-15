import fitz
import re
from collections import Counter

pdf_path = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Sri Aurobindo/TheFuturePoetry.pdf"
output_path = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Sri Aurobindo/TheFuturePoetry_clean.txt"

PAGE_OFFSET = 15

def is_page_number(s):
    return bool(re.fullmatch(r'\d+', s.strip()))

# Extract pages starting from PAGE_OFFSET
doc = fitz.open(pdf_path)
raw_pages = []
for i, page in enumerate(doc):
    if i < PAGE_OFFSET - 1:
        continue
    raw_pages.append(page.get_text("blocks"))  # use blocks, not raw text

print(f"Total pages in PDF: {len(doc)}")
print(f"Pages extracted (from page {PAGE_OFFSET}): {len(raw_pages)}")

# Detect repeating headers/footers
# First pass: collect all block texts to find repeats
all_block_texts = []
for page_blocks in raw_pages:
    for block in page_blocks:
        if block[6] == 0:  # text block (not image)
            text = block[4].strip()
            if text:
                all_block_texts.append(text)

block_counts = Counter(all_block_texts)

REPEAT_THRESHOLD = 10
MAX_HEADER_WORDS = 8

repeating_lines = {
    text for text, count in block_counts.items()
    if count >= REPEAT_THRESHOLD and len(text.split()) <= MAX_HEADER_WORDS
}

print(f"Repeating header/footer blocks detected: {len(repeating_lines)}")
for line in sorted(repeating_lines):
    print(f"  '{line}'")

# Collect blocks as paragraphs
seen_repeated = set()
paragraphs = []

for page_blocks in raw_pages:
    # Sort blocks by vertical position
    sorted_blocks = sorted(
        [b for b in page_blocks if b[6] == 0],
        key=lambda b: (b[1], b[0])
    )
    for block in sorted_blocks:
        text = block[4].strip()
        if not text:
            continue
        if is_page_number(text):
            continue
        if text in repeating_lines:
            if text in seen_repeated:
                continue
            else:
                seen_repeated.add(text)

        # Merge hyphenated line breaks within the block
        text = re.sub(r'-\n(\w)', r'\1', text)
        # Replace remaining newlines with spaces
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r' +', ' ', text).strip()

        if text:
            paragraphs.append(text)

with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n\n".join(paragraphs))

print(f"Done! {len(paragraphs)} paragraphs written to {output_path}")