import re
from pathlib import Path
from pypdf import PdfReader

PDF_PATH = Path("/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Nisargadatta Maharaj/I am that.pdf")
OUTPUT_PATH = Path("/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Nisargadatta Maharaj/I_Am_That_cleaned.txt")

START_PAGE = 8  # PDF page number, 1-based
START_HEADING = "1. The Sense of ‘I am’"

def clean_text(text):
    lines = text.splitlines()
    cleaned = []

    for line in lines:
        s = line.strip()

        if not s:
            cleaned.append("")
            continue

        # remove standalone page numbers
        if re.fullmatch(r"\d+", s):
            continue

        # remove tiny junk lines
        if len(s) <= 2 and not re.search(r"[A-Za-z]", s):
            continue

        cleaned.append(s)

    text = "\n".join(cleaned)

    # fix hyphenated line breaks
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # collapse extra blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # join lines into paragraphs but keep paragraph breaks
    paragraphs = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue

        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        merged = " ".join(lines)
        paragraphs.append(merged)

    return "\n\n".join(paragraphs).strip()

reader = PdfReader(str(PDF_PATH))
all_text = []

print(f"Extracting text from page {START_PAGE} to {len(reader.pages)}...")

started = False

for page_num in range(START_PAGE - 1, len(reader.pages)):
    page = reader.pages[page_num]
    raw = page.extract_text() or ""

    if not started:
        idx = raw.find(START_HEADING)
        if idx == -1:
            continue
        raw = raw[idx:]
        started = True

    cleaned = clean_text(raw)
    if cleaned:
        all_text.append(cleaned)

output = "\n\n".join(all_text)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(output)

print(f"Done! Written to:\n{OUTPUT_PATH}")
print(f"Total characters: {len(output):,}")