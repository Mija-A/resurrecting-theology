import re
from pypdf import PdfReader

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Dogen/Shobogenzo eBook 3.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Dogen/Shobogenzo_3_cleaned.txt"

START_PAGE = 16

def is_chinese(text):
    return any('\u4e00' <= c <= '\u9fff' for c in text)

def is_page_header(s):
    return bool(
        re.match(r"^[A-Z][\sA-Z\-]+\s{2,}\d+", s) or
        re.match(r"^\d+\s{2,}[A-Z][\sA-Z\-]+", s)
    )

def clean_page(text):
    lines = text.split("\n")
    cleaned = []
    in_footnote = False
    last_real_line = ""

    for line in lines:
        s = line.strip()

        # Whitespace-only line = footnote separator, but not after a page header
        if line and not s:
            if not is_page_header(last_real_line):
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

        if re.match(r"^\d+\.\s", s):
            in_footnote = True

        if is_page_header(s):
            in_footnote = False
            last_real_line = s
            continue

        # Chapter title (all-caps, no page number) also resets
        if in_footnote and re.fullmatch(r"[A-Z][A-Z\-O]+", s):
            in_footnote = False

        if in_footnote:
            continue

        last_real_line = s
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