import re
import subprocess

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Nisargadatta Maharaj/be_free.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Nisargadatta Maharaj/be_free_cleaned.txt"

START_PAGE = 6
END_PAGE = 125

def extract_text(pdf_path, start, end):
    result = subprocess.run(
        ["pdftotext", "-f", str(start), "-l", str(end), pdf_path, "-"],
        capture_output=True, text=True, encoding="utf-8"
    )
    return result.stdout

def clean(raw):
    poems = []
    for page in raw.split("\f"):
        lines = [l.strip() for l in page.split("\n")]
        cleaned = []
        for line in lines:
            if not line:
                continue
            # Skip recurring header lines
            if line == "BE FREE":
                continue
            if line == "108 Gems of Sri Nisargadatta Maharaj":
                continue
            cleaned.append(line)

        if not cleaned:
            continue

        # First line should be the poem number (standalone digit)
        if cleaned and re.fullmatch(r"\d+", cleaned[0]):
            num = cleaned[0]
            body = cleaned[1:]
        else:
            # No number found — skip (intro pages etc.)
            continue

        if body:
            poems.append(f"{num}\n" + "\n".join(body))

    return "\n\n".join(poems)

print("Extracting text...")
raw = extract_text(PDF_PATH, START_PAGE, END_PAGE)
output = clean(raw)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(output)

print(f"Done! Written to:\n{OUTPUT_PATH}")