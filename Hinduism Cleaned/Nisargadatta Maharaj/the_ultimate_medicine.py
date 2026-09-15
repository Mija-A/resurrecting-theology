import re
import os
import subprocess
import pytesseract
from PIL import Image, ImageOps, ImageFilter

Image.MAX_IMAGE_PIXELS = None  # disable decompression bomb check

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Nisargadatta Maharaj/the ultimate medicine.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Nisargadatta Maharaj/The_Ultimate_Medicine_cleaned.txt"

START_PAGE = 10
END_PAGE = 117

def render_pdf_page(page_num):
    prefix = f"/tmp/ultimate_medicine_{page_num}"
    subprocess.run([
        "pdftoppm",
        "-jpeg",
        "-r", "300",
        "-f", str(page_num),
        "-l", str(page_num),
        PDF_PATH,
        prefix
    ], check=True, capture_output=True)

    img_path = f"{prefix}-{page_num}.jpg"
    if not os.path.exists(img_path):
        candidates = sorted(
            f for f in os.listdir("/tmp")
            if f.startswith(f"ultimate_medicine_{page_num}") and f.endswith(".jpg")
        )
        if not candidates:
            return None
        img_path = os.path.join("/tmp", candidates[-1])

    return img_path

def preprocess(img):
    gray = ImageOps.grayscale(img)
    gray = ImageOps.autocontrast(gray)
    gray = gray.filter(ImageFilter.MedianFilter(size=3))
    bw = gray.point(lambda x: 0 if x < 185 else 255, mode="1")
    return bw

def split_spread(img):
    w, h = img.size
    mid = w // 2
    left = img.crop((0, 0, mid, h))
    right = img.crop((mid, 0, w, h))
    return [left, right]

def crop_text_region(page_img):
    """
    Crop away page margins so OCR does not read headers, footnotes, page numbers,
    and image captions near the borders.
    """
    w, h = page_img.size

    left_margin = int(w * 0.08)
    right_margin = int(w * 0.08)
    top_margin = int(h * 0.10)
    bottom_margin = int(h * 0.14)

    return page_img.crop((
        left_margin,
        top_margin,
        w - right_margin,
        h - bottom_margin
    ))

def ocr_page_half(img):
    cropped = crop_text_region(img)
    proc = preprocess(cropped)
    text = pytesseract.image_to_string(proc, lang="eng", config="--psm 4")
    return text

def looks_like_text(text):
    stripped = text.strip()
    if not stripped:
        return False

    letters = sum(c.isalpha() for c in stripped)
    words = re.findall(r"[A-Za-z]{2,}", stripped)

    if letters < 120:
        return False
    if len(words) < 25:
        return False

    return True

def is_footnote_line(s):
    s = s.strip()

    # obvious numbered footnote starts
    if re.match(r"^\d+\s+", s):
        return True

    # page number only
    if re.fullmatch(r"\d+", s):
        return True

    # roman numeral page number
    if re.fullmatch(r"[ivxlcdmIVXLCDM]+", s):
        return True

    # dictionary / glossary-like fragment lines often from bottom note area
    if re.search(r"\b(meaning|means|refers to|according to|signifies)\b", s, re.IGNORECASE):
        if len(s) < 180:
            return True

    # editorial or cross-reference note fragments
    if re.search(r"\b(see also|remarks on|present work|italics by editor|editor)\b", s, re.IGNORECASE):
        return True

    # isolated scholarly note fragments
    if re.search(r"\b(Hindu teachings|Absolute standpoint|consciousness turns in on itself)\b", s, re.IGNORECASE):
        return True

    return False

def clean_text(text):
    lines = text.split("\n")
    cleaned = []

    for line in lines:
        s = line.strip()

        if not s:
            cleaned.append("")
            continue

        # remove page numbers
        if re.fullmatch(r"\d+", s):
            continue
        if re.fullmatch(r"[ivxlcdmIVXLCDM]+", s):
            continue

        # remove running headers / repeated titles
        if re.search(r"\bThe Ultimate Medicine\b", s, re.IGNORECASE):
            continue
        if re.search(r"\bAs Prescribed by Sri Nisargadatta Maharaj\b", s, re.IGNORECASE):
            continue

        # remove photo caption / image credit lines
        if re.search(r"Photo by|courtesy of", s, re.IGNORECASE):
            continue
        if re.fullmatch(r"Sri\s+Nisargadatta\s+Maharaj", s, re.IGNORECASE):
            continue
        if re.fullmatch(r"1897\s*[-–]\s*1981", s):
            continue

        # remove chapter number by itself
        if re.fullmatch(r"\d+\.", s):
            continue

        # remove bottom footnote lines
        if is_footnote_line(s):
            continue

        # remove tiny OCR junk
        if len(s) <= 2 and not re.search(r"[A-Za-z]", s):
            continue

        cleaned.append(s)

    text = "\n".join(cleaned)

    # fix hyphenated line breaks
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # join lines into paragraphs, keep paragraph breaks
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

        paragraphs.append(merged)

    return "\n\n".join(paragraphs).strip()

print(f"Starting OCR on pages {START_PAGE}–{END_PAGE}...")
all_text = []

for page_num in range(START_PAGE, END_PAGE + 1):
    print(f"  Processing PDF spread {page_num}/{END_PAGE}...", end="\r")

    img_path = render_pdf_page(page_num)
    if not img_path:
        continue

    try:
        spread_img = Image.open(img_path)
        halves = split_spread(spread_img)

        for half in halves:
            raw = ocr_page_half(half)
            if looks_like_text(raw):
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