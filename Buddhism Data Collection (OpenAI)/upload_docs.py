import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

RELIGION_DIR = Path("buddhism")
MAP_FILE = Path("vector_stores.json")

if not RELIGION_DIR.exists():
    raise RuntimeError(f"Folder not found: {RELIGION_DIR}")

if MAP_FILE.exists():
    with open(MAP_FILE, "r", encoding="utf-8") as f:
        store_map = json.load(f)
else:
    store_map = {}

for scholar_dir in RELIGION_DIR.iterdir():
    if not scholar_dir.is_dir():
        continue

    scholar_name = scholar_dir.name
    files = [p for p in scholar_dir.iterdir() if p.is_file()]

    if not files:
        print(f"Skipping {scholar_name}: no files found")
        continue

    if scholar_name in store_map:
        vector_store_id = store_map[scholar_name]
        print(f"Using existing vector store for {scholar_name}: {vector_store_id}")
    else:
        store = client.vector_stores.create(name=f"buddhism::{scholar_name}")
        vector_store_id = store.id
        store_map[scholar_name] = vector_store_id
        print(f"Created vector store for {scholar_name}: {vector_store_id}")

    for path in files:
        print(f"Uploading {path}...", flush=True)
        with open(path, "rb") as f:
            client.vector_stores.files.upload_and_poll(
                vector_store_id=vector_store_id,
                file=f
            )
        print(f"Finished {path.name}")

with open(MAP_FILE, "w", encoding="utf-8") as f:
    json.dump(store_map, f, indent=2, ensure_ascii=False)

print("\nSaved vector store map to vector_stores.json")
print(json.dumps(store_map, indent=2, ensure_ascii=False))