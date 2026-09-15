import re
import unicodedata
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Adi Shankara Cleaning/Upadesa Sahasri.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Adi Shankara Cleaning/Upadesa_Sahasri_cleaned.txt"

START_PAGE = 8
END_PAGE = 322


# ── OCR ───────────────────────────────────────────────────────────────────────

def ocr_page(pdf_path, page_num):
    """Render one PDF page using pdf2image and OCR it with pytesseract."""
    imgs = convert_from_path(pdf_path, dpi=200, first_page=page_num, last_page=page_num)
    return pytesseract.image_to_string(imgs[0])


# ── TEXT NORMALIZATION ────────────────────────────────────────────────────────

def strip_diacritics(text):
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")

def fix_ocr(text):
    """Fix common OCR artifacts in English text."""
    text = re.sub(r'-\n([a-z])', r'\1', text)  # rejoin hyphenated line-breaks
    return text


# ── LINE CLASSIFIERS ──────────────────────────────────────────────────────────

def is_devanagari(s):
    return bool(re.search(r'[\u0900-\u097F]', s))

def is_sanskrit_ocr(s):
    """Latin-script OCR of Devanagari — pipe chars, verse markers, consonant noise."""
    if not s:
        return False
    # Sanskrit verse-end markers: | || Il ll
    if re.search(r'\||\bIl\b|\bll\b', s):
        return True
    # High non-ASCII ratio
    non_ascii = sum(1 for c in s if ord(c) > 127)
    if len(s) > 0 and non_ascii / len(s) > 0.35:
        return True
    return False

def is_running_header(s):
    """Running page headers contain ALL CAPS words AND a digit.
    e.g. 'A THOUSAND TEACHINGS  43', '3-9]  THE KNOWLEDGE  153'"""
    if re.search(r'[A-Z]{4,}', s) and re.search(r'\d', s):
        return True
    if re.match(r'^\d+[\-–]\d+\]', s):
        return True
    return False

def is_standalone_page_number(s):
    return bool(re.fullmatch(r'\d+', s))

def is_footnote(s):
    """Footnote lines. Patterns from this book:
       '+ After writing various books.'  (OCR reads * as +)
       '* Self-Knowledge.'
       '1Mu. U,, 1.2.'
       '1 After writing...'
       '1 eg., the Self.'
       'after. ®Chh. U,,'
    """
    if re.match(r'^[¹²³⁴⁵⁶⁷⁸⁹]\s', s): return True
    if re.match(r'^[\*\+†‡®@©°]\s*\S', s): return True
    if re.match(r'^\d[A-Z]', s): return True          # "1Mu.", "2Chh."
    if re.match(r'^\d\s+[A-Z][a-z]', s): return True  # "1 After writing..."
    if re.match(r'^\d\s+[a-z]', s): return True        # "1 eg., the Self."
    if re.match(r'^[A-Z][a-z]+\.\s+U\.', s): return True  # "Br. U., 1.5."
    return False

def is_chapter_title(s):
    """ALL CAPS chapter/part/section titles — no digits allowed.
    e.g. 'CHAPTER I', 'A METHOD OF ENLIGHTENING THE DISCIPLE', 'PART I (PROSE)'"""
    if not s:
        return False
    if not re.fullmatch(r'[A-Z][A-Z\s\(\)\-\.]+', s):
        return False
    if len(s) < 3 or len(s) > 80:
        return False
    if re.search(r'\d', s):        # digits = running header, not title
        return False
    if s in ("I", "II", "III", "IV", "A", "THE"):
        return False
    return True

def is_numbered_paragraph(s):
    """Starts a numbered English paragraph: '1. We shall...' '62. Disciple...'"""
    return bool(re.match(r'^\d+[\.\s]\s*[A-Za-z]', s))


# ── PAGE CLEANING ─────────────────────────────────────────────────────────────

def clean_page(ocr_text):
    """Extract only English content from one OCR'd page.

    Structure of this book:
      - Sanskrit block (bold Devanagari / OCR'd as garble)
      - Blank line
      - Numbered English paragraph
      - Blank line
      - Sanskrit block
      ... etc.
      - Footnotes at very bottom

    Blank lines always separate Sanskrit from English in this book,
    so resetting in_english on blank lines cleanly handles everything.
    """
    lines = ocr_text.split('\n')
    cleaned = []
    in_english = False
    in_footnote = False

    for line in lines:
        s = line.strip()

        if not s:
            # Blank line ends current paragraph and footnote block
            in_english = False
            in_footnote = False
            continue

        # Running header — strip silently, no state change
        if is_running_header(s):
            continue

        # Standalone page number
        if is_standalone_page_number(s):
            continue

        # Devanagari or Sanskrit OCR garbage
        if is_devanagari(s) or is_sanskrit_ocr(s):
            in_english = False
            continue

        # Footnote — skip block until next blank line
        if is_footnote(s):
            in_footnote = True
        if in_footnote:
            continue

        # Chapter/section title — always keep
        if is_chapter_title(s):
            cleaned.append(strip_diacritics(s))
            in_english = False
            continue

        # Numbered paragraph start
        if is_numbered_paragraph(s):
            in_english = True
            cleaned.append(fix_ocr(strip_diacritics(s)))
            continue

        # Continuation of English paragraph
        if in_english:
            cleaned.append(fix_ocr(strip_diacritics(s)))
            continue

        # Everything else — skip

    return "\n".join(cleaned).strip()


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Processing pages {START_PAGE}-{END_PAGE}...")

    output_blocks = []
    first_content_seen = False

    for page_num in range(START_PAGE, END_PAGE + 1):
        if page_num % 25 == 0:
            print(f"  Page {page_num}...")

        try:
            ocr_text = ocr_page(PDF_PATH, page_num)
        except Exception as e:
            print(f"  Warning: page {page_num} failed: {e}")
            continue

        cleaned = clean_page(ocr_text)

        if not cleaned:
            continue

        # Gate output until first numbered paragraph appears
        if not first_content_seen:
            if re.search(r'^\d+[\.\s]\s*[A-Za-z]', cleaned, re.MULTILINE):
                first_content_seen = True

        if first_content_seen or re.search(r'CHAPTER|PART|THOUSAND TEACHINGS', cleaned):
            output_blocks.append(cleaned)

    final_text = "\n\n".join(output_blocks)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(final_text)

    print(f"\nDone! {len(output_blocks)} pages written to:\n{OUTPUT_PATH}")


if __name__ == "__main__":
    main()