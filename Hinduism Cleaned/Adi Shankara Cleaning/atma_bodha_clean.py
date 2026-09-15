import re
import unicodedata
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Adi Shankara Cleaning/AtmaBodha (and Other Stotras).pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Adi Shankara Cleaning/AtmaBodha_cleaned.txt"

START_PAGE = 27
END_PAGE = 345


# OCR

def ocr_page(pdf_path, page_num):
    imgs = convert_from_path(pdf_path, dpi=200, first_page=page_num, last_page=page_num)
    return pytesseract.image_to_string(imgs[0])


# TEXT NORMALIZATION

def strip_diacritics(text):
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")

def fix_ocr(text):
    text = re.sub(r'-\n([a-z])', r'\1', text)  # rejoin hyphenated line-breaks
    return text


# LINE CLASSIFIERS

def is_devanagari(s):
    return bool(re.search(r'[\u0900-\u097F]', s))

def is_sanskrit_ocr(s):
    """OCR garbage of Devanagari rendered as Latin — pipe chars, high non-ASCII."""
    if not s:
        return False
    if re.search(r'\||\bIl\b|\bll\b', s):
        return True
    non_ascii = sum(1 for c in s if ord(c) > 127)
    if len(s) > 0 and non_ascii / len(s) > 0.35:
        return True
    # Sanskrit OCR consonant cluster patterns
    if re.search(r"(rr|ngr|mra|nta\..*nta|gga|ddi)", s) and not re.search(r"\b(centre|country|contract|entrance|contain|interest|introduce|connect)", s, re.I):
        return True
    return False

def is_running_header(s):
    """Running headers: 'SELF-KNOWLEDGE', 'APPENDIX', 'आत्मबोध:' etc.
    Pattern: short all-caps or Devanagari line with optional page number."""
    # All-caps short line with a digit (page num on same line)
    if re.search(r'[A-Z]{4,}', s) and re.search(r'\d', s):
        return True
    # Pure all-caps short line (running title without page number)
    if re.fullmatch(r'[A-Z][A-Z\s\-\.]+', s) and len(s) < 40:
        return True
    # Section range like "3-9]"
    if re.match(r'^\d+[\-–]\d+\]', s):
        return True
    return False

def is_standalone_page_number(s):
    return bool(re.fullmatch(r'\d+', s))

def is_verse_number_marker(s):
    """Verse number in brackets: [ 14 ] or (5) at end of stanza."""
    return bool(re.fullmatch(r'\[\s*\d+\s*\]', s) or re.fullmatch(r'\(\s*\d+\s*\)', s))

def is_footnote(s):
    if re.match(r'^[¹²³⁴⁵⁶⁷⁸⁹]\s', s): return True
    if re.match(r'^[\*\+†‡®@©°]\s*\S', s): return True
    if re.match(r'^\d[A-Z]', s): return True
    if re.match(r'^\d\s+[A-Z][a-z]', s): return True
    if re.match(r'^\d\s+[a-z]', s): return True
    if re.match(r'^[A-Z][a-z]+\.\s+U\.', s): return True
    return False

def is_chapter_title(s):
    """ALL CAPS chapter/section titles to keep once.
    e.g. 'INTRODUCTION', 'THE ORIGIN OF HINDU PHILOSOPHICAL THOUGHT', 'APPENDIX'
    No digits, not a running header (those are caught separately)."""
    if not s:
        return False
    if not re.fullmatch(r'[A-Z][A-Z\s\(\)\-\.]+', s):
        return False
    if len(s) < 4 or len(s) > 80:
        return False
    if re.search(r'\d', s):
        return False
    if s in ("I", "II", "III", "IV", "A", "THE"):
        return False
    return True

def is_mixed_case_title(s):
    """Mixed case section titles like '(Vedanta : Its Theory and Practice)'
    or 'THE ORIGIN OF HINDU PHILOSOPHICAL THOUGHT' subheadings."""
    if re.match(r'^\(.*\)$', s) and len(s) < 60:
        return True
    return False


# PAGE CLEANING

def clean_page(ocr_text, seen_titles):
    """Extract English content from one OCR'd page.

    This book is mostly continuous English prose. Structure:
    - Prose pages: running header + English paragraphs
    - Verse pages: [ N ] + Devanagari + English translation + commentary
    - Appendix pages: Devanagari stanza + English stanza + verse num (N)

    Strategy: skip Devanagari and Sanskrit OCR lines; keep everything else
    except running headers, page numbers, and footnotes.
    Chapter titles kept only on first occurrence.
    """
    lines = ocr_text.split('\n')
    cleaned = []
    in_footnote = False

    for line in lines:
        s = line.strip()

        if not s:
            in_footnote = False
            cleaned.append('')  # preserve paragraph breaks
            continue

        # Running header — skip silently
        if is_running_header(s):
            continue

        # Standalone page number
        if is_standalone_page_number(s):
            continue

        # Devanagari or Sanskrit OCR garbage — skip
        if is_devanagari(s) or is_sanskrit_ocr(s):
            continue

        # Footnote — skip block
        if is_footnote(s):
            in_footnote = True
        if in_footnote:
            continue

        # Verse number marker [ N ] — keep as section marker
        if is_verse_number_marker(s):
            cleaned.append(s)
            continue

        # Chapter title — keep only first occurrence
        if is_chapter_title(s):
            if s not in seen_titles:
                seen_titles.add(s)
                cleaned.append(strip_diacritics(s))
            continue

        # Mixed-case subtitle like "(Vedanta : Its Theory and Practice)"
        if is_mixed_case_title(s):
            cleaned.append(strip_diacritics(s))
            continue

        # Everything else is English content — keep it
        cleaned.append(fix_ocr(strip_diacritics(s)))

    # Clean up: collapse multiple blank lines to single
    result = re.sub(r'\n{3,}', '\n\n', '\n'.join(cleaned))
    return result.strip()


# MAIN

def main():
    print(f"Processing pages {START_PAGE}-{END_PAGE}...")

    output_blocks = []
    seen_titles = set()  # track chapter titles to avoid repeats

    for page_num in range(START_PAGE, END_PAGE + 1):
        if page_num % 25 == 0:
            print(f"  Page {page_num}...")

        try:
            ocr_text = ocr_page(PDF_PATH, page_num)
        except Exception as e:
            print(f"  Warning: page {page_num} failed: {e}")
            continue

        cleaned = clean_page(ocr_text, seen_titles)

        if cleaned:
            output_blocks.append(cleaned)

    final_text = "\n\n".join(output_blocks)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(final_text)

    print(f"\nDone! {len(output_blocks)} pages written to:\n{OUTPUT_PATH}")


if __name__ == "__main__":
    main()