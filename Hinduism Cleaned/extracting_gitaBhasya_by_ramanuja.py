import fitz
import pytesseract
import re
from PIL import Image
import io

pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'


def is_devanagari(text):
    return bool(re.search(r'[\u0900-\u097F]', text))

def clean_block(text):
    lines = text.split("\n")
    cleaned = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()

        if not s:
            i += 1
            continue

        # Skip Devanagari lines (Sanskrit original)
        if is_devanagari(s):
            i += 1
            continue

        # Skip standalone page numbers
        if re.fullmatch(r'\d+', s):
            i += 1
            continue

        # Skip running headers/footers like "1-8]  ARJUNA'S SPIRITUAL CONVERSION  45"
        if re.match(r'^\d+[-–]\d+\]', s):
            i += 1
            continue

        # Skip "ŚRĪ RĀMĀNUJA GĪTĀ BHĀṢYA" style running headers
        if re.search(r'GITA|BHASYA|RAMANUJA', s, re.IGNORECASE) and len(s) < 60:
            i += 1
            continue

        # Skip verse number markers like "|| 1 ||" standing alone
        if re.fullmatch(r'[\|\s\d]+', s):
            i += 1
            continue

        cleaned.append(s)
        i += 1

    return "\n".join(cleaned).strip()


def extract_text(
    pdf_path,
    output_path,
    start_page=14,
    stop_page=623,
):
    doc = fitz.open(pdf_path)
    output_blocks = []
    total = min(stop_page, len(doc)) - start_page

    print(f"Processing {total} pages ({start_page+1} to {min(stop_page, len(doc))})...")

    for page_idx in range(len(doc)):
        if page_idx < start_page:
            continue
        if page_idx >= stop_page:
            break

        page_num = page_idx + 1
        if (page_idx - start_page) % 20 == 0:
            print(f"  Processing page {page_num}...")

        page = doc[page_idx]

        # Render page as image at 300 DPI for good OCR quality
        mat = fitz.Matrix(300/72, 300/72)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))

        # OCR with English — use 'san' for Sanskrit detection if needed
        text = pytesseract.image_to_string(img, lang='eng')
        cleaned = clean_block(text)

        if not cleaned:
            continue

        # Split into verse segments
        segments = re.split(r'(?=^\s*\d+[\.\)]\s)', cleaned, flags=re.MULTILINE)

        page_parts = []
        for seg in segments:
            seg = seg.strip()
            if not seg:
                continue
            match = re.match(r'^(\d+)[\.\)]\s*(.*)', seg, re.DOTALL)
            if match:
                verse_num = match.group(1)
                verse_text = match.group(2).strip()
                page_parts.append(f"[Verse {verse_num}]\n{verse_text}")
            else:
                page_parts.append(seg)

        if page_parts:
            block = f"--- Page {page_num} ---\n" + "\n\n".join(page_parts)
            output_blocks.append(block)

    doc.close()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(output_blocks))

    print(f"\nDone! {len(output_blocks)} pages written to {output_path}")


# ---- CONFIGURE PATH ----
extract_text(
    pdf_path="/Users/mijasmacbookpro/Desktop/Prof Cantay Research/ Ramanuja_Gita_Bhasya.pdf",
    output_path="/Users/mijasmacbookpro/Desktop/Prof Cantay Research/extracted_ramanuja_gita_clean.txt",
    start_page=14,
    stop_page=623
)