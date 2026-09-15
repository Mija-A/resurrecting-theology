import re
from pypdf import PdfReader

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Nisargadatta Maharaj/Prior to Consciousness.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Nisargadatta Maharaj/Prior_to_Consciousness_cleaned.txt"

START_PAGE = 6
END_PAGE = 162

def extract_text(pdf_path, start, end):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages[start - 1 : end]:
        text += (page.extract_text() or "") + "\f"
    return text

def clean(raw):
    output_blocks = []

    for page in raw.split("\f"):
        lines = [l.rstrip() for l in page.split("\n")]
        cleaned = []

        for line in lines:
            s = line.strip()

            if not s:
                cleaned.append("")
                continue

            # Skip standalone page numbers
            if re.fullmatch(r"\d+", s):
                continue

            # Skip running headers: "N / PRIOR TO CONSCIOUSNESS" or "PRIOR TO C..NSCIOUSNESS / N"
            if re.search(r"PRIOR TO C[A-Z\.]+NSCIOUSNESS", s, re.IGNORECASE):
                continue

            cleaned.append(line)

        text = "\n".join(cleaned)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        if text:
            output_blocks.append(text)

    return "\n\n".join(output_blocks)

print("Extracting text...")
raw = extract_text(PDF_PATH, START_PAGE, END_PAGE)
output = clean(raw)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(output)

print(f"Done! Written to:\n{OUTPUT_PATH}")