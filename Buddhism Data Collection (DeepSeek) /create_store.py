import argparse
import json
import pickle
import re
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
STORES_DIR = Path("stores")
MAP_FILE = Path("vector_stores.json")


def slugify(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", text.strip()).strip("_") or "store"


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []

    chunks = []
    start = 0
    step = max(1, chunk_size - overlap)
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start += step
    return chunks


def load_txt_documents(folder: Path) -> list[dict]:
    documents = []
    for path in sorted(folder.iterdir()):
        if not path.is_file() or path.suffix.lower() != ".txt":
            continue

        text = path.read_text(encoding="utf-8").strip()
        for chunk_id, chunk in enumerate(chunk_text(text), start=1):
            documents.append({
                "source": path.name,
                "text": chunk,
                "chunk_id": chunk_id,
                "path": str(path),
            })
    return documents


def build_store(documents: list[dict], output_dir: Path, model_name: str = MODEL_NAME) -> None:
    if not documents:
        raise ValueError("No documents found to index.")

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)

    texts = [doc["text"] for doc in documents]
    print(f"Creating embeddings for {len(texts)} chunks...")
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    embeddings = embeddings.astype("float32")
    faiss.normalize_L2(embeddings)

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, str(output_dir / "faiss.index"))
    with open(output_dir / "metadata.pkl", "wb") as f:
        pickle.dump(documents, f)

    manifest = {
        "model_name": model_name,
        "num_chunks": len(documents),
        "sources": sorted({doc["source"] for doc in documents}),
    }
    with open(output_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def update_store_map(scholar: str, store_dir: Path) -> None:
    if MAP_FILE.exists():
        store_map = json.loads(MAP_FILE.read_text(encoding="utf-8"))
    else:
        store_map = {}

    store_map[scholar] = str(store_dir)
    MAP_FILE.write_text(json.dumps(store_map, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scholar", required=True, help='Example: "Adi Shankara"')
    parser.add_argument("--docs-dir", required=True, help="Folder containing that scholar's .txt files")
    parser.add_argument("--model-name", default=MODEL_NAME)
    args = parser.parse_args()

    docs_dir = Path(args.docs_dir)
    if not docs_dir.exists() or not docs_dir.is_dir():
        raise FileNotFoundError(f"Scholar folder not found: {docs_dir}")

    print(f"Loading documents from {docs_dir} ...")
    documents = load_txt_documents(docs_dir)
    print(f"Loaded {len(documents)} chunks.")

    scholar_slug = slugify(args.scholar)
    store_dir = STORES_DIR / scholar_slug
    build_store(documents, store_dir, args.model_name)
    update_store_map(args.scholar, store_dir)

    print(f"Saved store for {args.scholar} -> {store_dir}")
    print(f"Updated {MAP_FILE}")


if __name__ == "__main__":
    main()
