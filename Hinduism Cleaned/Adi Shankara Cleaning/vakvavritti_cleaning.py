import fitz
import pytesseract
import re
from PIL import Image
import io

pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'


# HELPERS

def has_devanagari(s):
    return bool(re.search(r'[\u0900-\u097F]', s))

def get_verse_num(s):
    # Strip leading non-digit chars (handles OCR artifacts like '_ 2.' or '= 3.')
    s_clean = re.sub(r'^[^0-9]+', '', s.strip())
    m = re.match(r'^([\d][\d,\s]*)\.\s+\S', s_clean)
    return m.group(1).strip() if m else None

ENGLISH_STARTERS = {
    'i','a','an','the','he','she','it','we','you','they','this','that',
    'these','those','there','here','what','when','where','who','how','why',
    'in','on','of','to','by','for','from','with','and','or','but','if',
    'as','be','is','are','was','were','has','have','had','do','does','did',
    'will','would','could','should','may','might','must','shall','no','not',
    'now','so','scorched','knowledge','thou','thus','just','even','such',
    'one','all','some','any','both','each','more','most','very','quite',
    'only','also','please','listen','explain','bow','know','give','make',
    'come','go','learn','ascertain','convince','unlike','owing','since',
    'through','after','before','like','according','while','at','up','my',
    'me','us','our','its','their','his','her','your','see','here','there',
    'consciousness','no','were','what',
}

def looks_mixed(s):
    """Detect numbered lines where Sanskrit OCR appears right after verse number."""
    # Strip leading artifacts before checking
    s_clean = re.sub(r'^[^0-9]+', '', s.strip())
    m = re.match(r'^[\d,\s]+\.\s+(.*)', s_clean)
    content = m.group(1) if m else s
    if not content: return False
    if content[0] in ('"', "'", '(', '\u201c', '\u2018', '\u2019', '\u201d'):
        return False
    words = content.split()
    if not words: return False
    first_raw = words[0]
    first = first_raw.rstrip(',:;#@!?')
    if first_raw.endswith(':') and len(first) <= 8:
        return True
    if first.lower() in ENGLISH_STARTERS:
        return False
    return True

def is_mixed_cont(s):
    """Detect continuation lines of mixed gloss (no verse number, but Sanskrit OCR mixed in)."""
    # @ symbol — never in clean English
    if '@' in s: return True
    # Digit-letter inside a word: q1t, 4Sfeq
    if re.search(r'[a-z]\d[a-zA-Z]', s): return True
    # lowerUPPER CamelCase OCR: faHe, aTd, afeq
    if re.search(r'\b[a-z]{2,}[A-Z][a-z]', s): return True
    # Letter + bracket: aaq], Af]
    if re.search(r'[a-zA-Z]{2,}\]', s): return True
    # < followed by digit: <4
    if re.search(r'<\d', s): return True
    # Hyphenated mixed-case chains: q1t-Ga-AETTET, faHe-aTd
    if re.search(r'[a-z]{2,}-[A-Z][a-z]+-[A-Z]{3,}|[A-Z]{3,}-[A-Z]{3,}[a-z]', s): return True
    # Repeated-letter OCR artifacts: aqq, aaq, fff
    if re.search(r'[a-z]qq|aa[a-z]{2,}|[a-z]{2}ff\b', s): return True
    return False

def is_running_header(s):
    if re.search(r'VAKYA\s*VRITTI|VAKYAVRITTI|VAKYAVRITT', s, re.IGNORECASE) and len(s) < 80:
        return True
    if re.match(r'^\[?(?:SL|st|su)[\.\s]*\d', s, re.IGNORECASE):
        return True
    return False

def is_standalone_page_number(s):
    return bool(re.fullmatch(r'\d{1,3}', s))

def is_footnote(s):
    if re.match(r'^[\*\†\+]\s', s): return True
    if re.match(r'^(Chh\.|Br\.|Tai\.|Ai\.|See\s|Ma\.|Bg\.|Bh\.|N\.|Mu\.|we\s\d|we\s[A-Z])', s): return True
    if re.match(r'^[1-6]\.\s+[A-Z]', s) and len(s) < 100: return True
    return False


# PAGE PROCESSING

def process_page(page_text, global_verse_seen, carry_in_english):
    """
    carry_in_english: carries across page boundary so continuations at top of
    next page are included. Blank lines within a page reset in_english.
    """
    lines = page_text.split('\n')
    kept = []
    in_english = carry_in_english
    page_started = False

    for line in lines:
        s = line.strip()

        if not s:
            if page_started:
                in_english = False
            continue

        page_started = True

        # Devanagari → reset and skip
        if has_devanagari(s):
            in_english = False
            continue

        # Running header → skip silently
        if is_running_header(s):
            continue

        # Standalone page number → skip silently
        if is_standalone_page_number(s):
            continue

        # Mixed continuation (Sanskrit OCR tokens mixed into English line)
        if is_mixed_cont(s):
            in_english = False
            continue

        # Verse number check (BEFORE footnote check)
        vnum = get_verse_num(s)
        if vnum:
            if looks_mixed(s):
                global_verse_seen[vnum] = global_verse_seen.get(vnum, 0) + 1
                in_english = False
            else:
                global_verse_seen[vnum] = global_verse_seen.get(vnum, 0) + 1
                in_english = True
                # Strip leading OCR artifacts before saving
                s_clean = re.sub(r'^[^0-9]+', '', s)
                kept.append(s_clean)
            continue

        # Footnote check (after verse check)
        if is_footnote(s):
            in_english = False
            continue

        # Continuation of English paragraph
        if in_english:
            kept.append(s)
            continue

    return '\n'.join(kept), in_english


def collapse_paragraphs(text):
    paragraphs = []
    current = []
    for line in text.split('\n'):
        if line.strip():
            current.append(line.strip())
        else:
            if current:
                paragraphs.append(' '.join(current))
                current = []
    if current:
        paragraphs.append(' '.join(current))
    return '\n\n'.join(paragraphs)


# MAIN

def extract_translation(
    pdf_path,
    output_path,
    start_page=10,
    stop_page=44,
    dpi=300,
):
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    end = min(stop_page, total_pages) if stop_page else total_pages

    print(f"PDF has {total_pages} pages. Processing pages {start_page + 1} to {end}...")

    output_blocks = []
    global_verse_seen = {}
    carry_in_english = False

    for page_idx in range(start_page, end):
        page_num = page_idx + 1

        if (page_idx - start_page) % 10 == 0:
            print(f"  → Page {page_num} / {end}...")

        page = doc[page_idx]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")

        raw = pytesseract.image_to_string(img, lang='eng')
        cleaned, carry_in_english = process_page(raw, global_verse_seen, carry_in_english)

        if not cleaned.strip():
            continue

        paragraphs = collapse_paragraphs(cleaned)
        if not paragraphs.strip():
            continue

        output_blocks.append(paragraphs)

    doc.close()

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(output_blocks))

    print(f"\nDone! {len(output_blocks)} pages written to:\n  {output_path}")


# RUN

extract_translation(
    pdf_path="/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Adi Shankara Cleaning/Vakvavritti.pdf",
    output_path="/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Adi Shankara Cleaning/Vakvavritti_translation_clean.txt",
    start_page=10,
    stop_page=44,
    dpi=300,
)