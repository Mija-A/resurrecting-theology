"""
Extract clean text from Orategama.pdf into Orategama_clean.txt.

What this script does:
  1. Extracts raw text from every page of the PDF
  2. Strips recurring headers, footers, and page numbers
  3. Normalises ALL-CAPS words to Title Case
  4. Fixes drop-cap artifacts: the PDF layout stored each paragraph's
     opening letter as a lone character on its own line, causing broken
     paragraph openers. This script removes those orphan letters and
     restores the correct first line for each affected paragraph.
  5. Fixes any remaining truncated paragraph openers (e.g. "esterday" -> "Yesterday")

Usage:
    python extract_orategama.py

Requires: pypdf  (installed automatically if missing)
"""

import re
import sys
from pathlib import Path

# -- Install pypdf if needed --------------------------------------------------
try:
    from pypdf import PdfReader
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pypdf", "-q"])
    from pypdf import PdfReader

# -- Paths --------------------------------------------------------------------
BASE_DIR = Path("/Users/mijasmacbookpro/Desktop/Prof Cantay Research/Buddhism Cleaned/Hakuin Ekaku")
PDF_PATH = BASE_DIR / "Orategama.pdf"
OUT_PATH = BASE_DIR / "Orategama_clean.txt"

# -- Lines to strip entirely --------------------------------------------------
STRIP_LINE_PATTERNS = [
    re.compile(r"^Zen\s+Master\s+Hakuin\s*:?\s*$", re.IGNORECASE),
    re.compile(r"^ORATEGAMA\s*\(\d+\)\s*$", re.IGNORECASE),
    re.compile(r"^Translated\s+by\s+Philip\s+B\.?\s+Yampolsky\s*$", re.IGNORECASE),
    re.compile(r"^HaKuin\s+Ekaku\s*[--]\s*Orategama\s*[--]\s*translation\s+by\s+Philip\s+B\.?\s+Yampolsky\s*(Page\s*\d+)?\s*$", re.IGNORECASE),
    re.compile(r"^Page\s+\d+\s*$", re.IGNORECASE),
    re.compile(r"^\d+\s*$"),
]

# -- Drop-cap fix map ---------------------------------------------------------
# The PDF stored each paragraph's opening letter as a lone line.
# The line immediately after it is the broken remainder of that paragraph's
# first line (missing the opening word). Both lines are replaced together
# with the correct full first line, keyed by the orphan's 0-based line index
# in the cleaned-but-not-yet-fixed text.
PARAGRAPH_STARTERS = {
    9:   "Yet if their motivation is bad, virtually all Zen practitioners find themselves blocked in both the active",
    52:  "Trivial and mundane matters pressed against my chest and a fire mounted in my heart. I was unable",
    99:  "For penetrating to the depths of one's own true self-nature, and for attaining a vitality valid on all",
    131: "The Hinayanists of old are frequently belittled. People of today, however, can scarcely attain to",
    221: "There are some blind, bald idiots who stand in a calm, unperturbed, untouchable place and",
    250: "When we consider the human condition as a whole, we see people who lack the merits to be",
    277: "Hakuyu used to say that, for the most part, the technique for nourishing the body is as follows:",
    406: "Do not say that worldly affairs and pressures of business have you no time to study Zen under",
    453: "In the middle ages when the Zen Sect flourished, samurai and high officials whose minds were",
    469: "I do not mean to say, however, that sitting in meditation should be despised or contemplation",
    503: "Under ordinary circumstances, service to a master means that you eat the master's food, wear",
    592: "What is this true meditation? It is to make everything: coughing, swallowing, waving the",
    689: "But the idiots of today do not understand. One often hears that band of blind, bald fools,",
    744: "How does one obtain true enlightenment? In the busy round of mundane affairs, in the",
    777: "In the past Ninagawa Shinuemon (144) gained a great awakening while involved in a fight. Ota",
    824: "In my later years I have come to the conclusion that the advantage in accomplishing true",
}

# Remaining truncated openers not covered by the drop-cap map above
TRUNCATED_FIXES = {
    "esterday I received": "Yesterday I received",
    "he Mo-ho chih-kuan":  "The Mo-ho chih-kuan",
}


# -- Helpers ------------------------------------------------------------------
def is_strip_line(line: str) -> bool:
    s = line.strip()
    return any(p.match(s) for p in STRIP_LINE_PATTERNS)


def normalize_caps(text: str) -> str:
    """Convert fully-uppercase words (2+ chars) to Title Case."""
    def fix_word(m):
        w = m.group(0)
        return w.title() if w.isupper() and len(w) > 1 else w
    return re.sub(r"\b[A-Z]{2,}\b", fix_word, text)


# -- Step 1: extract raw text -------------------------------------------------
def extract_pages(pdf_path: Path) -> list:
    reader = PdfReader(str(pdf_path))
    return [page.extract_text() or "" for page in reader.pages]


# -- Step 2: strip headers/footers, normalise caps, collapse blanks -----------
def clean_pages(pages: list) -> list:
    lines = []
    prev_blank = False
    for page_text in pages:
        for line in page_text.splitlines():
            if is_strip_line(line):
                continue
            line = normalize_caps(line)
            line = re.sub(r"[ \t]{2,}", " ", line)
            stripped = line.strip()
            if stripped == "":
                if not prev_blank:
                    lines.append("")
                prev_blank = True
            else:
                lines.append(stripped)
                prev_blank = False
    return lines


# -- Step 3: fix drop-cap orphans ---------------------------------------------
def fix_drop_caps(lines: list) -> list:
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r'^[A-Z]$', line.strip()) and i in PARAGRAPH_STARTERS:
            out.append(PARAGRAPH_STARTERS[i])
            i += 2  # skip orphan AND the broken next line
        else:
            out.append(line)
            i += 1
    return out


# -- Step 4: fix any remaining truncated openers ------------------------------
def fix_truncated(lines: list) -> list:
    out = []
    for line in lines:
        for bad, good in TRUNCATED_FIXES.items():
            if line.strip().startswith(bad):
                line = line.replace(bad, good, 1)
                break
        out.append(line)
    return out


# -- Main ---------------------------------------------------------------------
def main():
    if not PDF_PATH.exists():
        print("ERROR: PDF not found at {}".format(PDF_PATH), file=sys.stderr)
        sys.exit(1)

    print("Reading {} ...".format(PDF_PATH))
    pages = extract_pages(PDF_PATH)
    print("  {} pages found.".format(len(pages)))

    print("Cleaning ...")
    lines = clean_pages(pages)

    print("Fixing drop-cap artifacts ...")
    lines = fix_drop_caps(lines)
    lines = fix_truncated(lines)

    result = "\n".join(lines).strip()
    OUT_PATH.write_text(result, encoding="utf-8")
    print("Done. Written to {}  ({:,} chars)".format(OUT_PATH, len(result)))


if __name__ == "__main__":
    main()