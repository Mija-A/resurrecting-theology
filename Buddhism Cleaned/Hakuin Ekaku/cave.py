import re
from pypdf import PdfReader

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Hakuin Ekaku/cave.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Hakuin Ekaku/cave_clean.txt"

START_PAGE = 9

def clean_page(text):
    lines = text.split("\n")
    cleaned = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()

        if not s:
            i += 1
            continue

        # skip standalone page numbers
        if re.fullmatch(r"\d+", s):
            i += 1
            continue

        # merge single orphan letter onto next line (drop-cap artifact)
        # next line may start with lowercase OR uppercase continuation
        if re.match(r'^[A-Z]$', s) and i + 1 < len(lines):
            next_s = lines[i + 1].strip()
            if next_s and next_s[0].islower():
                cleaned.append(s + next_s)
                i += 2
                continue

        cleaned.append(s)
        i += 1

    # join the text and fix "P\nRECIOUS" style splits where P precedes an all-caps continuation
    result = "\n".join(cleaned)
    result = re.sub(r'\n([A-Z])\n([A-Z]{2,})', lambda m: '\n' + m.group(1) + m.group(2), result)

    return result

reader = PdfReader(PDF_PATH)
total = len(reader.pages)
print(f"Processing pages {START_PAGE}-{total}...")

blocks = []
for page in reader.pages[START_PAGE - 1:]:
    raw = page.extract_text() or ""
    cleaned = clean_page(raw)
    if cleaned:
        blocks.append(cleaned)

final = "\n\n".join(blocks)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(final)

print(f"Done - {len(blocks)} pages written to {OUTPUT_PATH}")