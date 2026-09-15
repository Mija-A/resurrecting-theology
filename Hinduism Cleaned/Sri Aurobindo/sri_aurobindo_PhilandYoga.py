import fitz
import re

pdf_path = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Sri Aurobindo/EssaysInPhilosophyAndYoga.pdf"
output_path = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Sri Aurobindo/EssaysInPhilosophyAndYoga_clean.txt"

PAGE_OFFSET = 15

def is_page_number(s):
    return bool(re.fullmatch(r'\d+', s.strip()))

def clean_block(text):
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if is_page_number(s):
            continue
        cleaned.append(line.rstrip())
    return "\n".join(cleaned).strip()

# ── Step 1: Extract text from PDF ─────────────────────────────────────────
doc = fitz.open(pdf_path)
raw_pages = []
for page in doc:
    raw_pages.append(page.get_text("text").strip())

# ── Step 2: Clean each page ────────────────────────────────────────────────
output_blocks = []
for page_text in raw_pages:
    cleaned = clean_block(page_text)
    if cleaned:
        output_blocks.append(cleaned)

with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n\n".join(output_blocks))

print(f"Done! {len(output_blocks)} non-empty pages written to {output_path}")
print(f"Pages {PAGE_OFFSET} to {PAGE_OFFSET + len(raw_pages) - 1}")