import re
from pypdf import PdfReader

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Dogen/Shobogenzo eBook 2.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Dogen/Shobogenzo_2_cleaned.txt"

START_PAGE = 18

def is_chinese(text):
    return any('\u4e00' <= c <= '\u9fff' for c in text)

def clean_page(text):
    lines = text.split("\n")
    cleaned = []
    in_footnote = False

    for line in lines:
        s = line.strip()

        # Line of only spaces = footnote separator in this PDF
        if line and not s:
            in_footnote = True
            continue

        if not s:
            if not in_footnote:
                cleaned.append("")
            continue

        if is_chinese(s):
            continue

        if re.fullmatch(r"\d+", s):
            continue

        if re.fullmatch(r"\[\d+\]", s):
            continue

        # Footnote starts with digit+dot
        if re.match(r"^\d+\.\s", s):
            in_footnote = True

        # Page header resets footnote state
        if re.match(r"^[A-Z\-]+\s{2,}\d+$", s) or re.match(r"^\d+\s{2,}[A-Z\-]+", s):
            in_footnote = False
            continue

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