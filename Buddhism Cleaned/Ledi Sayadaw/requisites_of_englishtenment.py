import re
import subprocess
from pathlib import Path

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Ledi Sayadaw/Requisites_of_Enlightement.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Ledi Sayadaw/Requisites_of_Enlightement_clean.txt"

START_PAGE = 13

def extract_text(pdf_path, start_page):
    result = subprocess.run(
        ["pdftotext", "-f", str(start_page), pdf_path, "-"],
        capture_output=True, text=True, encoding="utf-8"
    )
    return result.stdout

def is_footnote_trigger(line):
    s = line.strip()
    # horizontal rule
    if re.fullmatch(r"[_\-─—]{3,}", s):
        return True
    # one or more footnote numbers on a line, e.g. "4." or "4. 5." or "4. 5. 6."
    if re.fullmatch(r"(\d{1,2}\.\s*)+", s):
        return True
    return False

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

            # standalone page numbers
            if re.fullmatch(r"\d+", s):
                i += 1
                continue

            # roman numeral page numbers
            if re.fullmatch(r"[ivxlIVXL]+", s):
                i += 1
                continue

            # once we hit footnote territory, skip rest of page
            if is_footnote_trigger(lines[i]):
                in_footnote = True
                i += 1
                continue

            if in_footnote:
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

print(f"Extracting from page {START_PAGE}...")
raw = extract_text(PDF_PATH, START_PAGE)
cleaned = clean_text(raw)

Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(cleaned)

print(f"Done -> {OUTPUT_PATH}")