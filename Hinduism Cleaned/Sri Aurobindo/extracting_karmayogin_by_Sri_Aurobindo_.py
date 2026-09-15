import re

input_path = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Sri Aurobindo/karmayogin8_cleaned.txt"
output_path = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Sri Aurobindo/karmayogin8_cleaned.txt"

# The txt was extracted starting from PDF page index 19 (= book page 20).
# Each double-newline block = one PDF page.
# Block 0 = book page 20, block 1 = book page 21, etc.
PAGE_OFFSET = 20

def clean_block(text):
    lines = text.split("\n")
    cleaned = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()

        # Skip standalone page numbers
        if re.fullmatch(r'\d+', s):
            i += 1
            continue

        # Skip page markers like "--- Page 20 ---"
        if re.fullmatch(r'---\s*Page\s+\d+\s*---', s):
            i += 1
            continue

        # Skip "KARMAYOGIN / A WEEKLY REVIEW / of National Religion..." (3-line block)
        if s == "KARMAYOGIN":
            i += 3
            continue
        if s == "A WEEKLY REVIEW" or s.startswith("of National Religion"):
            i += 1
            continue

        # Skip "{ No. X" issue number lines
        if re.match(r'^\{ No\. \d+', s):
            i += 1
            continue

        # Skip "OTHER WRITINGS BY SRI AUROBINDO..." + following title lines until blank
        if re.match(r'^OTHER WRITINGS BY SRI AUROBINDO IN (THIS ISSUE|ISSUES)', s):
            i += 1
            while i < len(lines) and lines[i].strip() != "":
                i += 1
            continue

        # Skip "Karmayogin no. X, date" lines
        if re.match(r'^Karmayogin no\. \d+', s):
            i += 1
            continue

        # Skip footnote/source attribution lines
        if re.search(r'---\s*Page\s+\d+\s*---', s):            
            i += 1
            continue
        if re.match(r'^(and republished|in three issues|in two issues|in the Bengalee)', s, re.IGNORECASE):
            i += 1
            continue
        if re.match(r'^(Text published|republished|Published in|Originally published)', s, re.IGNORECASE):
            i += 1
            continue
        if re.match(r'^(Speech delivered|Delivered at|Address delivered)', s, re.IGNORECASE):
            i += 1
            continue
        if re.match(r'^English-language newspaper', s):
            i += 1
            continue

        # Skip repeating standalone "Karmayogin" header
        if s == "Karmayogin":
            i += 1
            continue

        if s:
            cleaned.append(lines[i].rstrip())
        i += 1

    return "\n".join(cleaned).strip()


with open(input_path, "r", encoding="utf-8") as f:
    raw = f.read()

pages = raw.split("\n\n")

output_blocks = []
for idx, page_text in enumerate(pages):
    page_num = idx + PAGE_OFFSET
    cleaned = clean_block(page_text)
    if cleaned:
        output_blocks.append(cleaned)

with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n\n".join(output_blocks))

print(f"Done! {len(output_blocks)} pages written to {output_path}")
print(f"Pages {PAGE_OFFSET} to {PAGE_OFFSET + len(pages) - 1}")