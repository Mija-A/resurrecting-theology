import re
import os
import shutil
import subprocess
import pytesseract
from PIL import Image, ImageOps, ImageFilter

Image.MAX_IMAGE_PIXELS = None

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Ramanuja/theoryOfKnowledge.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Ramanuja/Theory_of_Knowledge_cleaned.txt"

START_PAGE = 5
END_PAGE = 232

def check_setup():
    if not os.path.exists(PDF_PATH):
        raise FileNotFoundError(f"PDF not found:\n{PDF_PATH}")

    if shutil.which("pdftoppm") is None:
        raise RuntimeError(
            "pdftoppm is not installed or not in PATH.\n"
            "Install with: brew install poppler"
        )

    if shutil.which("tesseract") is None:
        raise RuntimeError(
            "tesseract is not installed or not in PATH.\n"
            "Install with: brew install tesseract"
        )

def render_pdf_page(page_num):
    prefix = f"/tmp/theory_page_{page_num}"
    result = subprocess.run([
        "pdftoppm",
        "-jpeg",
        "-r", "300",
        "-f", str(page_num),
        "-l", str(page_num),
        PDF_PATH,
        prefix
    ], capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(
            f"pdftoppm failed on page {page_num}\n\n"
            f"STDERR:\n{result.stderr}\n\n"
            f"STDOUT:\n{result.stdout}"
        )

    candidates = sorted(
        os.path.join("/tmp", f)
        for f in os.listdir("/tmp")
        if f.startswith(f"theory_page_{page_num}") and f.endswith(".jpg")
    )

    if not candidates:
        raise RuntimeError(f"No JPG output created for page {page_num}")

    return candidates[-1]

def crop_text_area(img):
    w, h = img.size

    left = int(w * 0.08)
    right = int(w * 0.94)
    top = int(h * 0.04)
    bottom = int(h * 0.92)   # cuts off most footnotes/page-bottom junk

    return img.crop((left, top, right, bottom))

def preprocess(img):
    gray = ImageOps.grayscale(img)
    gray = ImageOps.autocontrast(gray)
    gray = gray.filter(ImageFilter.MedianFilter(size=3))
    bw = gray.point(lambda x: 0 if x < 185 else 255, mode="1")
    return bw

def ocr_page(img):
    processed = preprocess(img)
    return pytesseract.image_to_string(processed, lang="eng", config="--psm 4")

def clean_text(text):
    lines = text.split("\n")
    cleaned = []

    for line in lines:
        s = line.strip()

        if not s:
            cleaned.append("")
            continue

        # remove standalone page numbers
        if re.fullmatch(r"\d+", s):
            continue

        # remove roman numeral page numbers
        if re.fullmatch(r"[ivxlcdmIVXLCDM]+", s):
            continue

        # remove running headers like:
        # "2 SRI RAMANUJA'S THEORY OF KNOWLEDGE"
        if re.fullmatch(r"\d+\s+SRI\s+RAMANUJA'?S\s+THEORY\s+OF\s+KNOWLEDGE", s, re.IGNORECASE):
            continue

        # remove short running headers like "PERCEPTION 3"
        if re.fullmatch(r"[A-Z][A-Z\s'-]{2,}\s+\d+", s):
            continue

        # remove obvious footnote lines
        if re.match(r"^\d+\.\s", s):
            continue
        if re.match(r"^\d+\s+[A-Z]", s):
            continue

        # remove bottom junk / scan stamp fragments
        if re.search(r"S\.?\s*V\.?\s*O\.?\s*COLLEGE", s, re.IGNORECASE):
            continue

        # normalize spaces
        s = s.replace("\t", " ")
        s = re.sub(r"\s{2,}", " ", s)

        # remove tiny junk
        if len(s) <= 2 and not re.search(r"[A-Za-z]", s):
            continue

        cleaned.append(s)

    text = "\n".join(cleaned)

    # fix hyphenated line breaks
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # join lines into paragraphs, keeping paragraph breaks
    paragraphs = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue

        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        merged = ""

        for ln in lines:
            if not merged:
                merged = ln
            elif re.search(r"[-–—]$", merged):
                merged += ln
            else:
                merged += " " + ln

        merged = re.sub(r"\s{2,}", " ", merged).strip()
        if merged:
            paragraphs.append(merged)

    return "\n\n".join(paragraphs).strip()

check_setup()

print(f"Starting OCR on pages {START_PAGE}–{END_PAGE}...")
all_text = []

for page_num in range(START_PAGE, END_PAGE + 1):
    print(f"  Processing page {page_num}/{END_PAGE}...", end="\r")

    img_path = render_pdf_page(page_num)

    try:
        img = Image.open(img_path)
        img = crop_text_area(img)
        raw = ocr_page(img)
        cleaned = clean_text(raw)

        if cleaned:
            all_text.append(cleaned)

    finally:
        if os.path.exists(img_path):
            os.remove(img_path)

output = "\n\n".join(all_text)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(output)

print(f"\nDone! Written to:\n{OUTPUT_PATH}")
print(f"Total characters: {len(output):,}")