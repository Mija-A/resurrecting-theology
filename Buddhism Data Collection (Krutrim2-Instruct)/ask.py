import argparse
import csv
import json
import pickle
import random
import re
import time
from pathlib import Path

import faiss
import numpy as np
import requests
from sentence_transformers import SentenceTransformer

MAP_FILE = Path("vector_stores.json")
OUTPUT_DIR = Path("results")
RETRIEVER_MODEL_NAME = "all-MiniLM-L6-v2"
GENERATION_MODEL_NAME = "krutrim-2"
TOP_K = 1
LLAMA_URL = "http://127.0.0.1:8080/completion"

RELIGION_CONFIG = {
    "Hindu": {
        "identity_label": "Hindu",
        "dominant_religion": "Hinduism",
        "countries": ["Bangladesh", "India", "Pakistan", "Sri Lanka"],
    },
    "Hinduism": {
        "identity_label": "Hindu",
        "dominant_religion": "Hinduism",
        "countries": ["Bangladesh", "India", "Pakistan", "Sri Lanka"],
    },
    "Buddhist": {
        "identity_label": "Buddhist",
        "dominant_religion": "Buddhism",
        "countries": [
            "China", "Japan", "Malaysia", "Indonesia", "Philippines",
            "South Korea", "Singapore", "Taiwan", "Thailand", "Vietnam"
        ],
    },
    "Buddhism": {
        "identity_label": "Buddhist",
        "dominant_religion": "Buddhism",
        "countries": [
            "China", "Japan", "Malaysia", "Indonesia", "Philippines",
            "South Korea", "Singapore", "Taiwan", "Thailand", "Vietnam"
        ],
    },
    "Confucian": {
        "identity_label": "Confucian",
        "dominant_religion": "Confucianism",
        "countries": [
            "China", "Japan", "Malaysia", "Indonesia", "Philippines",
            "South Korea", "Singapore", "Taiwan", "Thailand", "Vietnam"
        ],
    },
    "Confucianism": {
        "identity_label": "Confucian",
        "dominant_religion": "Confucianism",
        "countries": [
            "China", "Japan", "Malaysia", "Indonesia", "Philippines",
            "South Korea", "Singapore", "Taiwan", "Thailand", "Vietnam"
        ],
    },
}

NATIONALITY_MAP = {
    "Bangladesh": "Bangladeshi",
    "China": "Chinese",
    "India": "Indian",
    "Indonesia": "Indonesian",
    "Japan": "Japanese",
    "Malaysia": "Malaysian",
    "Pakistan": "Pakistani",
    "Philippines": "Filipino",
    "South Korea": "South Korean",
    "Singapore": "Singaporean",
    "Sri Lanka": "Sri Lankan",
    "Taiwan": "Taiwanese",
    "Thailand": "Thai",
    "Vietnam": "Vietnamese",
}


def load_store_map():
    with open(MAP_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_questions(questions_path: Path):
    with open(questions_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_local_store(store_dir: Path):
    index_file = store_dir / "faiss.index"
    metadata_file = store_dir / "metadata.pkl"

    if not index_file.exists() or not metadata_file.exists():
        raise FileNotFoundError(f"Missing FAISS store files in {store_dir}")

    index = faiss.read_index(str(index_file))

    with open(metadata_file, "rb") as f:
        documents = pickle.load(f)

    return index, documents


def retrieve(query: str, model, index, documents, k: int = TOP_K):
    query_embedding = model.encode([query], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(query_embedding)
    _, indices = index.search(query_embedding, k)

    results = []
    seen = set()

    for i in indices[0]:
        if 0 <= i < len(documents):
            key = (documents[i].get("source", ""), documents[i].get("chunk_id"))
            if key not in seen:
                results.append(documents[i])
                seen.add(key)

    return results


def extract_number(text: str):
    # (?<!\d) prevents grabbing the digit after an en-dash in ranges like "1–4",
    # which would otherwise be read as "-4". Genuine negatives like -3 still match
    # because they are preceded by a space or start of string, not a digit.
    matches = re.findall(r"(?<!\d)-?\d+(?:\.\d+)?", text.strip())
    if not matches:
        return -99
    value = float(matches[-1])
    # -3 is a WVS "not applicable" system code — remap to -99
    if value == -3:
        return -99
    return int(value) if value == int(value) else value


def is_non_numeric_question(coding: str) -> bool:
    """Returns True for questions that cannot produce a valid numeric response."""
    non_numeric_markers = ["ISO code", "Enter country"]
    return any(marker in coding for marker in non_numeric_markers)


def build_prompt(religion: str, scholar: str, question: str, coding: str) -> str:
    return (
        f"I am a {religion} scholar named {scholar}. Based on my works, answer with only a number.\n"
        f"Question: {question}\n"
        f"Coding: {coding}\n"
        f"Answer:"
    )


def format_retrieved_context(retrieved_docs):
    chunks = []

    for i, doc in enumerate(retrieved_docs, start=1):
        text = (
            doc.get("text")
            or doc.get("chunk_text")
            or doc.get("content")
            or ""
        ).strip()

        source = doc.get("source", f"chunk_{i}")
        chunk_id = doc.get("chunk_id", i)

        if text:
            chunks.append(f"[Source: {source} | Chunk: {chunk_id}]\n{text}")

    return "\n\n---\n\n".join(chunks)


def ask_model(prompt, retrieved_docs):

    context_text = format_retrieved_context(retrieved_docs)

    full_prompt = (
        f"Retrieved context:\n{context_text}\n\n"
        f"{prompt}"
    )

    response = requests.post(
        LLAMA_URL,
        json={
            "prompt": full_prompt,
            "n_predict": 50,
            "temperature": 0.0,
            "stop": [],
        },
        timeout=300,
    )

    response.raise_for_status()

    data = response.json()

    return data.get("content", "").strip()


def get_religion_context(religion):
    if religion not in RELIGION_CONFIG:
        raise ValueError(
            f"No built-in config for religion '{religion}'. "
            f"Supported: {', '.join(sorted(RELIGION_CONFIG.keys()))}"
        )
    return RELIGION_CONFIG[religion]


def expand_question_variants(question_obj, religion):
    context = get_religion_context(religion)
    identity_label = context["identity_label"]
    dominant_religion = context["dominant_religion"]
    countries = context["countries"]

    question_text = question_obj["question"]
    coding_text = question_obj["coding"]

    has_nationality = "[nationality]" in question_text or "[nationality]" in coding_text
    has_dom_religion = "[dominant religion]" in question_text or "[dominant religion]" in coding_text
    has_religion = "[religion]" in question_text or "[religion]" in coding_text

    if not has_nationality and not has_dom_religion and not has_religion:
        return [{
            "question": question_text,
            "coding": coding_text,
            "country_context": "",
            "nationality_context": "",
            "dominant_religion_context": "",
            "identity_label_context": "",
            "is_placeholder_expansion": 0,
        }]

    variants = []

    for country in countries:
        nationality = NATIONALITY_MAP[country]

        q = (
            question_text
            .replace("[dominant religion]", identity_label)
            .replace("[religion]", identity_label)
            .replace("[nationality]", nationality)
        )
        c = (
            coding_text
            .replace("[dominant religion]", identity_label)
            .replace("[religion]", identity_label)
            .replace("[nationality]", nationality)
        )

        variants.append({
            "question": q,
            "coding": c,
            "country_context": country,
            "nationality_context": nationality,
            "dominant_religion_context": dominant_religion,
            "identity_label_context": identity_label,
            "is_placeholder_expansion": 1,
        })

    return variants


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scholar", required=True)
    parser.add_argument("--religion", required=True)
    parser.add_argument("--rounds", default=5, type=int)
    parser.add_argument("--seed", default=42, type=int)
    parser.add_argument("--questions", default="wvs_questions.json")
    parser.add_argument("--survey-name", default="")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    questions_path = Path(args.questions)
    store_map = load_store_map()
    questions = load_questions(questions_path)

    if args.scholar not in store_map:
        raise KeyError(f"Scholar '{args.scholar}' not found in {MAP_FILE}")

    store_dir = Path(store_map[args.scholar])
    index, documents = load_local_store(store_dir)
    retriever_model = SentenceTransformer(RETRIEVER_MODEL_NAME)

    survey_name = args.survey_name or questions_path.stem

    safe_scholar = args.scholar.replace(" ", "_")
    safe_model = GENERATION_MODEL_NAME.replace(".", "_")
    safe_survey = survey_name.replace(" ", "_")
    safe_religion = args.religion.replace(" ", "_")
    output_file = OUTPUT_DIR / f"{safe_survey}_{safe_religion}_{safe_scholar}_{safe_model}_{args.rounds}rounds.csv"

    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "survey",
            "scholar",
            "religion",
            "model",
            "round",
            "question_order_position",
            "question_id",
            "variable",
            "scale_type",
            "country_context",
            "nationality_context",
            "dominant_religion_context",
            "identity_label_context",
            "is_placeholder_expansion",
            "question",
            "coding",
            "raw_response",
            "numeric_response",
        ])

        for round_num in range(1, args.rounds + 1):
            print(f"\nROUND {round_num}\n")

            round_questions = questions[:]
            random.Random(args.seed + round_num).shuffle(round_questions)

            order_pos = 0

            for q in round_questions:
                variants = expand_question_variants(q, args.religion)

                for variant in variants:
                    order_pos += 1

                    # Skip non-numeric questions (e.g. ISO country code fields)
                    if is_non_numeric_question(variant["coding"]):
                        writer.writerow([
                            survey_name,
                            args.scholar,
                            args.religion,
                            GENERATION_MODEL_NAME,
                            round_num,
                            order_pos,
                            q["id"],
                            q.get("variable", ""),
                            q.get("scale_type", ""),
                            variant["country_context"],
                            variant["nationality_context"],
                            variant["dominant_religion_context"],
                            variant["identity_label_context"],
                            variant["is_placeholder_expansion"],
                            variant["question"],
                            variant["coding"],
                            "SKIPPED",
                            -99,
                        ])
                        print(
                            f"round={round_num} "
                            f"order={order_pos} "
                            f"qid={q['id']} "
                            f"country={variant['country_context'] or '-'} "
                            f"raw='SKIPPED' numeric=-99 [non-numeric question]"
                        )
                        continue

                    retrieval_query = f"{variant['question']} {variant['coding']}"
                    retrieved_docs = retrieve(
                        retrieval_query,
                        retriever_model,
                        index,
                        documents,
                        TOP_K
                    )

                    prompt = build_prompt(
                        args.religion,
                        args.scholar,
                        variant["question"],
                        variant["coding"],
                    )

                    raw_answer = ask_model(prompt, retrieved_docs)
                    numeric_answer = extract_number(raw_answer)

                    writer.writerow([
                        survey_name,
                        args.scholar,
                        args.religion,
                        GENERATION_MODEL_NAME,
                        round_num,
                        order_pos,
                        q["id"],
                        q.get("variable", ""),
                        q.get("scale_type", ""),
                        variant["country_context"],
                        variant["nationality_context"],
                        variant["dominant_religion_context"],
                        variant["identity_label_context"],
                        variant["is_placeholder_expansion"],
                        variant["question"],
                        variant["coding"],
                        raw_answer,
                        numeric_answer,
                    ])

                    print(
                        f"round={round_num} "
                        f"order={order_pos} "
                        f"qid={q['id']} "
                        f"country={variant['country_context'] or '-'} "
                        f"raw={raw_answer!r} "
                        f"numeric={numeric_answer!r}"
                    )

                    time.sleep(0.4)

    print(f"\nSaved → {output_file}")


if __name__ == "__main__":
    main()