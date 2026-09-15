import re
import os
import shutil
import subprocess
import pytesseract
import cv2
import numpy as np
from PIL import Image, ImageOps, ImageFilter

Image.MAX_IMAGE_PIXELS = None

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Ramanuja/Anjali.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Ramanuja/Anjali_Apr_2007_english_cleaned.txt"

START_PAGE = 15
END_PAGE = 53

def check_setup():
    if not os.path.exists(PDF_PATH):
        raise FileNotFoundError(f"PDF not found:\n{PDF_PATH}")

    if shutil.which("pdftoppm") is None:
        raise RuntimeError(
            "pdftoppm is not installed or not in PATH.\n"
            "Install Poppler with:\n"
            "brew install poppler"
        )

    if shutil.which("tesseract") is None:
        raise RuntimeError(
            "tesseract is not installed or not in PATH.\n"
            "Install it with:\n"
            "brew install tesseract"
        )

def render_pdf_page(page_num):
    prefix = f"/tmp/anjali_{page_num}"

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
        if f.startswith(f"anjali_{page_num}") and f.endswith(".jpg")
    )

    if not candidates:
        raise RuntimeError(f"No JPG output created for page {page_num}")

    return candidates[-1]

def crop_main_text_area(img):
    w, h = img.size
    return img.crop((
        int(w * 0.06),
        int(h * 0.06),
        int(w * 0.96),
        int(h * 0.95)
    ))

def preprocess_for_ocr(img):
    gray = ImageOps.grayscale(img)
    gray = ImageOps.autocontrast(gray)
    gray = gray.filter(ImageFilter.MedianFilter(size=3))
    return gray

def remove_boxed_regions(pil_img):
    img = np.array(pil_img)
    gray = img if len(img.shape) == 2 else cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.threshold(blur, 200, 255, cv2.THRESH_BINARY_INV)[1]
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    h, w = gray.shape
    mask = np.zeros_like(gray)

    for cnt in contours:
        x, y, cw, ch = cv2.boundingRect(cnt)
        area = cw * ch

        if area < 0.03 * w * h:
            continue
        if area > 0.80 * w * h:
            continue

        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.03 * peri, True)

        if len(approx) == 4:
            cv2.rectangle(mask, (x, y), (x + cw, y + ch), 255, -1)

    cleaned = gray.copy()
    cleaned[mask == 255] = 255
    return Image.fromarray(cleaned)

def ocr_page(img):
    processed = preprocess_for_ocr(img)
    processed = remove_boxed_regions(processed)
    return pytesseract.image_to_string(processed, lang="eng", config="--psm 4")

def mostly_english(text):
    letters = re.findall(r"[A-Za-z]", text)
    non_latin = re.findall(r"[^\x00-\x7F]", text)

    if len(letters) < 120:
        return False

    return len(letters) >= max(40, len(non_latin) * 2)

def should_skip_page(text):
    low = text.lower()

    if "crossword" in low:
        return True
    if "answers to the crossword" in low:
        return True
    if "children's special" in low or "childrens special" in low:
        return True
    if "quiz questions" in low:
        return True
    if not mostly_english(text):
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

        if re.fullmatch(r"\d+", s):
            continue

        ascii_letters = len(re.findall(r"[A-Za-z]", s))
        non_ascii = len(re.findall(r"[^\x00-\x7F]", s))
        if non_ascii > ascii_letters and non_ascii > 3:
            continue

        if re.fullmatch(r"ANJALI", s, re.IGNORECASE):
            continue
        if re.search(r"Vishishtadvaita Pracharini Trust", s, re.IGNORECASE):
            continue
        if re.search(r"Issue\s*-\s*\d+", s, re.IGNORECASE):
            continue
        if re.search(r"Volume\s*-\s*\d+", s, re.IGNORECASE):
            continue
        if re.search(r"April\s*-\s*2007", s, re.IGNORECASE):
            continue
        if re.search(r"Across|Down|Answers to the Crossword", s, re.IGNORECASE):
            continue

        s = s.replace("\t", " ")
        s = re.sub(r"\s{2,}", " ", s)

        if len(s) <= 2 and not re.search(r"[A-Za-z]", s):
            continue

        cleaned.append(s)

    text = "\n".join(cleaned)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    paragraphs = []
    for block in text.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        merged = " ".join(lines)
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
        img = crop_main_text_area(img)
        raw = ocr_page(img)

        if should_skip_page(raw):
            continue

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