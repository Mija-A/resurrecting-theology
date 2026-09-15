import re
from pypdf import PdfReader

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Hakuin Ekaku/Hakuin-Heart-Sutra.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Hakuin Ekaku/Hakuin-Heart-Sutra_clean.txt"

START_PAGE = 9  # skip front matter (cover, about, portrait, title, copyright, dedication, contents, publisher's note)

# Words that legitimately appear at end of lines — don't strip their trailing space-split
REAL_WORDS = {
    'a','an','in','of','on','to','the','and','but','for','nor','yet','so',
    'by','at','as','is','or','it','be','we','he','she','up','no','do','go',
    'its','was','are','has','had','not','any','all','can','may','if','my',
    'us','our','from','with','that','this','than','then','when','they',
    'their','there','have','been','will','would','could','should','which',
    'into','onto','over','under','about','after','through'
}

def clean_page(text):
    lines = text.split("\n")
    cleaned = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # skip blank lines
        if not line:
            i += 1
            continue

        # skip standalone page numbers
        if re.fullmatch(r"\d+", line):
            i += 1
            continue

        # single orphan letter on its own line — merge onto next line
        if re.match(r'^[A-Za-z]$', line) and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line and next_line[0].islower():
                cleaned.append(line + next_line)
                i += 2
                continue

        # fix mid-word space split caused by justified typesetting:
        # "W ords" -> "Words", "Y amanashi" -> "Yamanashi", "an d" -> "and"
        # Rule: if line ends with "X Y" where Y is 1-4 chars and not a real word, remove the space
        m = re.search(r'([a-zA-Z]) ([a-z]{1,4})$', line)
        if m and m.group(2) not in REAL_WORDS:
            line = line[:m.start(1) + 1] + line[m.start(2):]

        # single trailing letter split (e.g. "tex t" -> "text")
        line = re.sub(r'([a-z]) ([a-z])$', lambda m: m.group(1) + m.group(2), line)

        # fix mid-line capital splits: "W ords" -> "Words", "V ehicle" -> "Vehicle"
        line = re.sub(r'\b([A-Z]) ([a-z]{2,})\b', lambda m: m.group(1) + m.group(2), line)

        # fix apostrophe splits: "Tortoise' s" -> "Tortoise's"
        line = re.sub(r"(\w)' s\b", r"\1's", line)

        cleaned.append(line)
        i += 1

    return "\n".join(cleaned)


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