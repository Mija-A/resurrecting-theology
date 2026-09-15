import re
from pypdf import PdfReader

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Dogen/daily_sutras_Fukanzazengi.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Dogen/Fukanzazengi_cleaned.txt"

START_PAGE = 1

def clean_page(text):
    lines = text.split("\n")
    cleaned = []

    for line in lines:
        s = line.strip()

        if not s:
            cleaned.append("")
            continue

        # Skip standalone page numbers
        if re.fullmatch(r"\d+", s):
            continue

        # Skip footer lines: "SAN FRANCISCO ZEN CENTER" or license badge text
        if re.search(r"SAN FRANCISCO ZEN CENTER", s, re.IGNORECASE):
            continue
        if re.search(r"BY-NC-ND|CC\s+BY", s):
            continue

        cleaned.append(line.rstrip())

    text = "\n".join(cleaned)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text

reader = PdfReader(PDF_PATH)
total = len(reader.pages)
print(f"Processing pages {START_PAGE}–{total}...")

blocks = []
for page in reader.pages[START_PAGE - 1:]:
    raw = page.extract_text() or ""
    cleaned = clean_page(raw)
    if cleaned:
        blocks.append(cleaned)

final = "\n\n".join(blocks)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(final)

print(f"Done — {len(blocks)} pages written to {OUTPUT_PATH}")