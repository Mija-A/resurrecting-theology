import argparse
import json
import re
from pathlib import Path

from create_store import build_store, load_txt_documents

DEFAULT_RELIGION_DIR = Path("hinduism")
STORES_DIR = Path("stores")
MAP_FILE = Path("vector_stores.json")


def slugify(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", text.strip()).strip("_") or "store"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--religion-dir", default=str(DEFAULT_RELIGION_DIR), help='Example: "hinduism" or "buddhism"')
    parser.add_argument("--rebuild", action="store_true", help="Rebuild stores even if they already exist")
    args = parser.parse_args()

    religion_dir = Path(args.religion_dir)
    if not religion_dir.exists() or not religion_dir.is_dir():
        raise RuntimeError(f"Folder not found: {religion_dir}")

    if MAP_FILE.exists():
        store_map = json.loads(MAP_FILE.read_text(encoding="utf-8"))
    else:
        store_map = {}

    STORES_DIR.mkdir(exist_ok=True)

    for scholar_dir in sorted(religion_dir.iterdir()):
        if not scholar_dir.is_dir():
            continue

        scholar_name = scholar_dir.name
        documents = load_txt_documents(scholar_dir)
        if not documents:
            print(f"Skipping {scholar_name}: no .txt files found")
            continue

        scholar_slug = slugify(scholar_name)
        store_dir = STORES_DIR / scholar_slug

        if store_dir.exists() and not args.rebuild:
            print(f"Using existing local store for {scholar_name}: {store_dir}")
        else:
            print(f"Building local store for {scholar_name} ...")
            build_store(documents, store_dir)
            print(f"Finished {scholar_name}")

        store_map[scholar_name] = str(store_dir)

    MAP_FILE.write_text(json.dumps(store_map, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved store map to {MAP_FILE}")
    print(json.dumps(store_map, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
