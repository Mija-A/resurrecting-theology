import re
import subprocess
from pathlib import Path

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Ledi Sayadaw/The-Manual-of-Dhamma-by-Ven.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Ledi Sayadaw/The-Manual-of-Dhamma-by-Ven_clean.txt"

START_PAGE = 16 

def extract_text(pdf_path, start_page):
    result = subprocess.run(
        ["pdftotext", "-f", str(start_page), pdf_path, "-"],
        capture_output=True, text=True, encoding="utf-8"
    )
    return result.stdout

def clean_text(text):
    pages = text.split("\f")
    blocks = []

    for page in pages:
        lines = page.split("\n")
        cleaned = []
        in_footnote = False
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

            # skip roman numeral page numbers
            if re.fullmatch(r"[ivxlIVXL]+", s):
                i += 1
                continue

            # horizontal rule signals start of footnote section
            if re.fullmatch(r"[_\-─—]{3,}", s):
                in_footnote = True
                i += 1
                continue

            # once in footnote zone, skip everything
            if in_footnote:
                i += 1
                continue

            # also catch footnotes that appear without a rule:
            # lines starting with a superscript-style number + text, e.g. "3 Asankheyya: ..."
            if re.match(r'^\d{1,2}\s+[A-Z*]', s) and len(s) < 200:
                i += 1
                continue

            # merge dangling list markers onto next line
            if re.fullmatch(r"([\divxlIVXL]+)\.", s) and i + 1 < len(lines):
                nxt = lines[i + 1].strip()
                if nxt:
                    cleaned.append(s + " " + nxt)
                    i += 2
                    continue

            cleaned.append(s)
            i += 1

        block = "\n".join(cleaned).strip()
        if block:
            blocks.append(block)

    return "\n\n".join(blocks)

print(f"Extracting from page {START_PAGE}…")
raw = extract_text(PDF_PATH, START_PAGE)
cleaned = clean_text(raw)

Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(cleaned)

print(f"Done → {OUTPUT_PATH}")