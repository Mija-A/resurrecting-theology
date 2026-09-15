import re
from pathlib import Path
from pypdf import PdfReader

PDF_PATH = Path("/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Nisargadatta Maharaj/nisargadatta gita.pdf")
OUTPUT_PATH = Path("/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Nisargadatta Maharaj/Nisargadatta_Gita_cleaned.txt")

START_PAGE = 11  # PDF page number, 1-based

def normalize_whitespace(text):
    text = text.replace("\t", " ")
    text = text.replace("\u00A0", " ")
    text = text.replace("\u2002", " ")
    text = text.replace("\u2003", " ")
    text = text.replace("\u2009", " ")
    text = text.replace("\u202F", " ")
    return text

def clean_text(text):
    text = normalize_whitespace(text)
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

        # remove book title / author / contact info lines
        if re.fullmatch(r"The Nisargadatta Gita", s, re.IGNORECASE):
            continue
        if re.fullmatch(r"Pradeep Apte", s, re.IGNORECASE):
            continue
        if re.fullmatch(r"aptep@yahoo\.com", s, re.IGNORECASE):
            continue
        if re.fullmatch(r"apte98@gmail\.com", s, re.IGNORECASE):
            continue

        # remove tiny junk lines
        if len(s) <= 2 and not re.search(r"[A-Za-z0-9]", s):
            continue

        # collapse repeated spaces inside line
        s = re.sub(r"\s{2,}", " ", s)

        cleaned.append(s)

    text = "\n".join(cleaned)

    # fix hyphenated line breaks
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # join lines into paragraphs but keep paragraph breaks
    paragraphs = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue

        lines = [re.sub(r"\s{2,}", " ", ln.strip()) for ln in block.split("\n") if ln.strip()]
        merged = " ".join(lines)
        merged = re.sub(r"\s{2,}", " ", merged).strip()
        paragraphs.append(merged)

    return "\n\n".join(paragraphs).strip()

reader = PdfReader(str(PDF_PATH))
all_text = []

print(f"Extracting text from page {START_PAGE} to {len(reader.pages)}...")

for page_num in range(START_PAGE - 1, len(reader.pages)):
    page = reader.pages[page_num]
    raw = page.extract_text() or ""
    cleaned = clean_text(raw)

    if cleaned:
        all_text.append(cleaned)

output = "\n\n".join(all_text)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(output)

print(f"Done! Written to:\n{OUTPUT_PATH}")
print(f"Total characters: {len(output):,}")