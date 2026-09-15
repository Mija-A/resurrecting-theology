import re
import unicodedata
from pypdf import PdfReader

PDF_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Adi Shankara Cleaning/Bhagavad_Gita.pdf"
OUTPUT_PATH = "/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Adi Shankara Cleaning/Bhagavad_gita_cleaned.txt"

START_PAGE = 17
END_PAGE = 538

def extract_text(pdf_path, start, end):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages[start - 1:end]:
        text += (page.extract_text() or "") + "\f"
    return text

def strip_diacritics(text):
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")

def normalize_line(s):
    """Fix common OCR artifacts before classification."""
    s = s.replace('\u00b7', '.')   # middle dot → period
    s = s.replace('\u00ad', '')    # soft hyphen
    s = s.replace('\u00a3', 'f')   # £ → f (OCR misread)
    s = re.sub(r'^r\.(\s)', r'1.\1', s)  # "r. What" → "1. What"
    return s

def fix_ocr(text):
    """Fix italic/cursive letter OCR artifacts (backslash sequences, l( patterns)."""
    fixes = [
        # Krishna variants — must come before generic rules
        (r'\bl\(\?\s*\.\.\s*ishna', 'Krishna'),
        (r'\bI\\ris1ta\b', 'Krishna'),
        (r'\bI\\rishna\b', 'Krishna'),
        # Named word fixes — specific before generic
        (r'\bl\\tladhava\b', 'Madhava'),
        (r'\bl\\tle\b', 'Me'),
        (r'\b1\\1e\b', 'Me'),
        (r'\b1\\1([A-Za-z])', lambda m: 'M' + m.group(1)),  # 1\1anu → Manu
        (r'\bl\\t([a-z])', lambda m: 'M' + m.group(1)),     # other l\t
        (r'\bI\\f', 'M'),           # I\fahadeva → Mahadeva
        # two / how
        (r'\bt\\VO\b', 'two'),
        (r'\bt\\vo\b', 'two'),
        (r'\bho\\V\b', 'how'),
        (r'\bho\\.v\b', 'how'),
        # W / w — italic W as \V or \v
        (r'\\V', 'W'),
        (r'\\v', 'w'),
        # Whatever — V\;h
        (r'\bV\\;h', 'Wh'),
        # \IV → W
        (r'\\IV', 'W'),
        # l( → K
        (r'\bl\(ing\b', 'King'),
        (r'\bl\(esava\b', 'Kesava'),
        (r'\bl\(', 'K'),
        # Misc
        (r'J\\.nd\b', 'And'),
        (r'\bH-\\s\b', 'Has'),
        (r"De\\'ata", 'Devata'),
        (r'\bO\\Yn\b', 'Own'),
        (r'a\\lsterity', 'austerity'),
        (r'ris1ta', 'rishna'),
        (r'\bI\\r', 'Kr'),
        (r"Kshet'[lr]'a", 'Kshetra'),
        (r"Kshet'[lr]'", 'Kshetr'),
        (r"e'\\j'en", 'even'),
        (r'\bl\\1e\b', 'Me'),       # l\1e → Me
        (r'\\tV', 'W'),              # \tVhen → When
        (r'\b0\\Yn\b', 'Own'),      # 0\Yn → Own (digit 0 variant)
        (r' \\s\b', ' '),            # trailing \s noise
    ]
    for pat, rep in fixes:
        if callable(rep):
            text = re.sub(pat, rep, text)
        else:
            text = re.sub(pat, rep, text)
    return text

RUNNING_HEADERS = re.compile(
    r'^(THE\s+BHAGA\s*VA\s*D[\-\xb7\s\.]*GIT[A\xc2]\.?'
    r'|THE\s+BHAGAVAD[\-\s]GITA\.?'
    r'|!HE\s+BHAGAVAD\s+GITA\.?'
    r')$', re.IGNORECASE)

PAGE_HEADER = re.compile(
    r'^\d[\d\-\)\]\s]*[A-Z]{3}.{5,}\d+\s*$'
    r'|^[\d\-\)\]\s]+THE\s+[A-Z]', re.IGNORECASE)

def is_sanskrit_line(s):
    """s should be normalize_line'd before calling."""
    if not s:
        return False
    if re.fullmatch(r'\d+[\-–]?\d*\.', s):
        return False
    if re.search(r'[^\x00-\x7F]', s):
        return True
    if re.fullmatch(r'[\s"\'`~\^*\.,;:\-\(\)\[\]\\\/\{\}|=\d]+', s):
        return True
    if len(re.findall(r'[~=+:<>{}\[\]\\|]', s)) >= 2:
        return True
    words = re.findall(r'[A-Za-z]{3,}', s)
    if words:
        garbage = sum(1 for w in words
                      if len(re.findall(r'[aeiouAEIOU]', w)) / len(w) < 0.15)
        if garbage / len(words) > 0.5:
            return True
    return False

def is_standalone_verse_number(s):
    m = re.fullmatch(r'(\d+)[\-–]?(\d*)\.', s)
    if not m:
        return False
    if int(m.group(1)) > 80:
        return False
    return True

def is_speaker_label(s):
    if len(s) > 35:
        return False
    return bool(re.match(r'^([A-Z][A-Za-z]+\s*){1,3}[Ss]aid\s*:', s))

def is_boilerplate(s):
    if re.fullmatch(r'\d+', s):
        return True
    if re.fullmatch(r'[\d]+[-\u2013][\d]+[\]\}]', s) or re.fullmatch(r'[\d]+[\]\}]', s):
        return True
    if RUNNING_HEADERS.match(s):
        return True
    if re.fullmatch(r'[IVX]+\.?', s):
        return True
    if re.fullmatch(r'[\[\(]?Drs?\.?\s+[IVX]+\.?[\]\)]?', s, re.IGNORECASE):
        return True
    return False

def is_page_header(s):
    return bool(PAGE_HEADER.match(s))

def is_chapter_title(s):
    if not re.fullmatch(r'[A-Z][A-Z\s\'\-\.\xb7~]+', s):
        return False
    if len(s) > 80 or re.search(r'\d', s):
        return False
    if s in ("I", "A", "THE", "WITH", "II", "III"):
        return False
    return True

def is_subheading(s):
    if not re.fullmatch(r"[A-Z][A-Za-z' \-]+", s):
        return False
    if len(s) > 70 or re.search(r'\d', s):
        return False
    if re.search(r'[,;:()\[\]]', s):
        return False
    if re.search(r'\b(is|are|was|were|be|has|have|had|does|do|not|cannot|leads|comes|makes|shows|means|implies|refers|teaches|says|said|proves|follows|explains)\b', s, re.IGNORECASE):
        return False
    return True

def is_footnote_start(s):
    return bool(re.match(r'^[\*\u2022\u2020]\s', s))

def clean_block(text, first_verse_seen=True):
    lines = text.split("\n")
    cleaned = []
    i = 0
    in_verse = False
    in_footnote = False
    pending_verse_num = None

    while i < len(lines):
        s = normalize_line(lines[i].strip())

        if not s:
            in_footnote = False
            i += 1
            continue

        if is_page_header(s):
            i += 1
            continue

        if is_sanskrit_line(s):
            if not pending_verse_num:
                in_verse = False
            i += 1
            continue

        if is_boilerplate(s):
            i += 1
            continue

        if is_footnote_start(s):
            in_footnote = True
        if in_footnote:
            i += 1
            continue

        if is_standalone_verse_number(s):
            pending_verse_num = s
            i += 1
            continue

        if re.match(r'^\d+[\-–]?\d*\.\s+\S', s):
            pending_verse_num = None
            in_verse = True
            cleaned.append(fix_ocr(strip_diacritics(s)))
            i += 1
            continue

        if is_speaker_label(s):
            pending_verse_num = None
            in_verse = True
            cleaned.append(fix_ocr(strip_diacritics(s)))
            i += 1
            continue

        if is_chapter_title(s):
            cleaned.append(strip_diacritics(s))
            i += 1
            continue

        if is_subheading(s):
            if first_verse_seen:
                cleaned.append(fix_ocr(strip_diacritics(s)))
            i += 1
            continue

        if pending_verse_num and not is_sanskrit_line(s) and first_verse_seen:
            in_verse = True
            cleaned.append(fix_ocr(strip_diacritics(pending_verse_num + " " + s)))
            pending_verse_num = None
            i += 1
            continue

        if in_verse:
            cleaned.append(fix_ocr(strip_diacritics(s)))
            i += 1
            continue

        i += 1

    return "\n".join(cleaned).strip()


print("Extracting text from PDF...")
raw = extract_text(PDF_PATH, START_PAGE, END_PAGE)
pages = raw.split("\f")

output_blocks = []
first_verse_seen = False

for idx, page_text in enumerate(pages):
    cleaned = clean_block(page_text, first_verse_seen)
    if cleaned:
        if re.search(r'^\d+[\-\u2013]?\d*\.\s+\S', cleaned, re.MULTILINE):
            first_verse_seen = True
        if first_verse_seen or re.search(r'DISCOURSE|INTRODUCTION|YOGA', cleaned):
            output_blocks.append(cleaned)

final_text = "\n\n".join(output_blocks)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(final_text)

print(f"Done! {len(output_blocks)} pages written.")
print(f"Output: {OUTPUT_PATH}")