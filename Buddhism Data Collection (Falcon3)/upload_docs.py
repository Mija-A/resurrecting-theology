from __future__ import annotations

import json
import pickle
import re
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

DOCS_DIR = Path("docs")
MAP_FILE = Path("vector_stores.json")
RETRIEVER_MODEL_NAME = "all-MiniLM-L6-v2"
MAX_CHARS = 1200


def split_into_chunks(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if not current:
            current = sentence
        elif len(current) + 1 + len(sentence) <= max_chars:
            current = f"{current} {sentence}"
        else:
            chunks.append(current)
            current = sentence

    if current:
        chunks.append(current)

    return chunks


def load_text_files(scholar_dir: Path) -> list[dict]:
    txt_files = sorted(scholar_dir.glob("*.txt"))
    if not txt_files:
        raise FileNotFoundError(f"No .txt files found in {scholar_dir}")

    docs = []
    for path in txt_files:
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue

        chunks = split_into_chunks(text)
        if not chunks:
            chunks = [text[:MAX_CHARS]]

        for i, chunk in enumerate(chunks):
            docs.append(
                {
                    "source": path.stem,
                    "chunk_id": f"{path.stem}_chunk_{i}",
                    "text": chunk,
                }
            )

    if not docs:
        raise ValueError(f"All .txt files in {scholar_dir} were empty.")

    return docs


def build_store(docs: list[dict], store_dir: Path) -> None:
    store_dir.mkdir(parents=True, exist_ok=True)

    model = SentenceTransformer(RETRIEVER_MODEL_NAME)
    texts = [d["text"] for d in docs]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=True,
    ).astype("float32")

    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, str(store_dir / "faiss.index"))

    with open(store_dir / "metadata.pkl", "wb") as f:
        pickle.dump(docs, f)


def main() -> None:
    if not DOCS_DIR.exists():
        raise FileNotFoundError(f"Docs directory not found: {DOCS_DIR.resolve()}")

    scholar_dirs = sorted([p for p in DOCS_DIR.iterdir() if p.is_dir()])
    if not scholar_dirs:
        raise FileNotFoundError(
            "Expected scholar subfolders inside docs/, e.g. docs/Scholar_Name/*.txt"
        )

    store_map = {}

    for scholar_dir in scholar_dirs:
        scholar_name = scholar_dir.name
        store_dir = Path("vector_store") / scholar_name

        print(f"\nProcessing scholar: {scholar_name}")
        docs = load_text_files(scholar_dir)
        print(f"  Loaded {len(docs)} chunks")
        build_store(docs, store_dir)

        store_map[scholar_name] = str(store_dir)

    with open(MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(store_map, f, ensure_ascii=False, indent=2)

    print(f"\nSaved vector store map to: {MAP_FILE.resolve()}")


if __name__ == "__main__":
    main()