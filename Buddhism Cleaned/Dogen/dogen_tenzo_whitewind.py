import re
from pypdf import PdfReader

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Dogen/Dogen-Tenzo-WhiteWind.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Dogen/Tenzo_Kyokun_cleaned.txt"

START_PAGE = 1

def clean_page(text):
    lines = text.split("\n")
    cleaned = []
    in_footnote = False

    for line in lines:
        s = line.strip()

        if not s:
            cleaned.append("")
            in_footnote = False
            continue

        # Skip standalone page numbers
        if re.fullmatch(r"\d+", s):
            continue

        # Skip title/header lines
        if re.search(r"Tenzo [Kk]yokun", s):
            continue
        if re.search(r"Eihei Dogen|Anzan Hoshin|Yasuda Joshu|White Wind|Great Matter Publications", s):
            continue
        if re.search(r"\[published in", s):
            continue

        # Detect footnote block
        if re.match(r"^\d+\.\s+[A-Z]", s):
            in_footnote = True
        if in_footnote:
            continue

        # Remove inline footnote superscripts
        line = re.sub(r"(?<=\w)\d+(?=[\s,\.\"\u201d]|$)", "", line)
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