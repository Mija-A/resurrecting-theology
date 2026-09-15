"""
yasenkanna_extract.py
---------------------
Extracts both translations from Yasenkanna2.pdf sequentially:
  - Part 1: Norman Waddell's translation (left column, x=46-296)
  - Part 2: Trevor Leggett's translation (middle column, x=296-535)

The PDF is a three-column table: Waddell | Leggett | I Ching ref.
Column boundaries are consistent across all pages.

Requirements:
    pip install pdfplumber

Usage:
    python yasenkanna_extract.py

Input:  Yasenkanna2.pdf             (same folder as this script)
Output: Yasenkanna_both.txt         (same folder as this script)
"""

import re
import pdfplumber

PDF_PATH    = "Yasenkanna2.pdf"
OUTPUT_PATH = "Yasenkanna_both.txt"

# Pages to process (1-indexed). Page 1 is a cover page with no table content.
START_PAGE = 2
END_PAGE   = 25

# Column x boundaries (consistent across all pages)
WADDELL_X_MIN  = 0.0
WADDELL_X_MAX  = 296.0
LEGGETT_X_MIN  = 296.0
LEGGETT_X_MAX  = 535.0

# extraction

def extract_column(pdf_path, start_page, end_page, x_min, x_max):
    """
    Extract words falling within the given x range across all pages,
    reconstruct lines by y-position, then paragraphs by vertical gap.
    """
    all_paragraphs = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num in range(start_page - 1, min(end_page, len(pdf.pages))):
            page = pdf.pages[page_num]

            words = [
                w for w in page.extract_words(x_tolerance=3, y_tolerance=3)
                if w["x0"] >= x_min and w["x0"] < x_max
            ]
            if not words:
                continue

            # Group into lines by y-coordinate (tolerance = 3pt)
            words.sort(key=lambda w: (round(w["top"] / 3), w["x0"]))
            lines, current = [], [words[0]]
            for w in words[1:]:
                if abs(w["top"] - current[0]["top"]) <= 3:
                    current.append(w)
                else:
                    lines.append(current)
                    current = [w]
            lines.append(current)

            # Detect paragraph breaks from larger-than-normal vertical gaps
            tops = [l[0]["top"] for l in lines]
            gaps = [tops[i+1] - tops[i] for i in range(len(tops) - 1)]
            avg_gap = sum(gaps) / len(gaps) if gaps else 12

            rendered = [" ".join(w["text"] for w in line) for line in lines]
            paragraphs, block = [], [rendered[0]]
            for i, text in enumerate(rendered[1:], start=1):
                if tops[i] - tops[i - 1] > avg_gap * 1.6:
                    paragraphs.append(" ".join(block))
                    block = [text]
                else:
                    block.append(text)
            paragraphs.append(" ".join(block))

            all_paragraphs.extend(paragraphs)

    return all_paragraphs


# cleaning

FOOTER = re.compile(
    r"(Master Hakuin.s Yasen Kanna\s*[–\-]\s*2 translations compiled|Lecut in 2011 Page)",
    re.IGNORECASE
)

SKIP_PATTERNS = [
    re.compile(r"Norman Waddell|Trevor Legett", re.IGNORECASE),
    re.compile(r"Master HAKUIN.s YASEN", re.IGNORECASE),
    re.compile(r"^YASENKANNA(\s+By Hakuin)?$", re.IGNORECASE),
    re.compile(r"^By Hakuin$", re.IGNORECASE),
    re.compile(r"^\(in (Wild Ivy|Second Zen reader)\)$", re.IGNORECASE),
    re.compile(r"^Idle Talk on a Night Boat$", re.IGNORECASE),
    re.compile(r"^Page\s*\d+$"),
    re.compile(r"^(I\s+Ching|ref\.|Hex\s*#?\d+)$", re.IGNORECASE),
]

def clean(paragraphs):
    out = []
    for p in paragraphs:
        if FOOTER.search(p):
            continue
        if any(pat.search(p.strip()) for pat in SKIP_PATTERNS):
            continue

        # Normalize quotes / dashes
        p = p.replace("\u2018", "'").replace("\u2019", "'")
        p = p.replace("\u201c", '"').replace("\u201d", '"')
        p = p.replace("\u2014", "--").replace("\u2013", "-")

        # Fix known extraction quirks
        p = p.replace(" y everyday", " my everyday")

        p = re.sub(r"  +", " ", p).strip()
        if p:
            out.append(p)
    return out


# main

def main():
    print(f"Reading {PDF_PATH} ...")

    print("  Extracting Waddell (left column)...")
    waddell = clean(extract_column(PDF_PATH, START_PAGE, END_PAGE, WADDELL_X_MIN, WADDELL_X_MAX))

    print("  Extracting Leggett (middle column)...")
    leggett = clean(extract_column(PDF_PATH, START_PAGE, END_PAGE, LEGGETT_X_MIN, LEGGETT_X_MAX))

    waddell_text = "\n\n".join(waddell).strip()
    leggett_text = "\n\n".join(leggett).strip()

    sep = "=" * 60
    output = (
        "YASENKANNA\n"
        + "Norman Waddell's Translation (in Wild Ivy)\n"
        + sep + "\n\n"
        + waddell_text
        + "\n\n\n"
        + sep + "\n"
        + "Trevor Leggett's Translation (in Second Zen Reader)\n"
        + sep + "\n\n"
        + leggett_text
    )

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"Done. Written to: {OUTPUT_PATH}")
    print(f"Waddell: {len(waddell_text.split()):,} words")
    print(f"Leggett: {len(leggett_text.split()):,} words")

if __name__ == "__main__":
    main()