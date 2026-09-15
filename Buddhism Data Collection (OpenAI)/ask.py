
import os
import json
import csv
import re
import time
import argparse
import random
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

MAP_FILE = Path("vector_stores.json")
OUTPUT_DIR = Path("results")
MODEL_NAME = "gpt-5.4-mini"

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


def extract_number(text: str) -> str:
    match = re.search(r"-?\d+(\.\d+)?", text.strip())
    return match.group(0) if match else ""


def build_prompt(religion: str, scholar: str, question: str, coding: str) -> str:
    return (
        f"I am an {religion} scholar named {scholar}. "
        "Please respond to questions based solely on information extracted from my works. "
        "The response should contain only a single numerical value and nothing else.\n\n"
        f"Question:\n{question}\n\n"
        f"Response coding:\n{coding}"
    )


def ask_model(vector_store_id: str, prompt: str) -> str:
    response = client.responses.create(
        model=MODEL_NAME,
        input=prompt,
        tools=[{
            "type": "file_search",
            "vector_store_ids": [vector_store_id]
        }]
    )
    return response.output_text.strip()


def get_religion_context(religion: str):
    if religion not in RELIGION_CONFIG:
        raise ValueError(
            f"No built-in config for religion '{religion}'. "
            f"Supported: {', '.join(sorted(RELIGION_CONFIG.keys()))}"
        )
    return RELIGION_CONFIG[religion]


def expand_question_variants(question_obj: dict, religion: str):
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
    parser.add_argument("--scholar", required=True, help='Example: "Adi Shankara"')
    parser.add_argument("--religion", required=True, help='Example: "Hindu"')
    parser.add_argument("--rounds", default=5, type=int)
    parser.add_argument("--seed", default=42, type=int)
    parser.add_argument("--questions", default="wvs_questions.json")
    parser.add_argument("--survey-name", default="")

    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    questions_path = Path(args.questions)
    if not questions_path.exists():
        raise FileNotFoundError(f"Questions file not found: {questions_path}")

    store_map = load_store_map()
    questions = load_questions(questions_path)

    if args.scholar not in store_map:
        raise KeyError(f"Scholar '{args.scholar}' not found in vector_stores.json")

    vector_store_id = store_map[args.scholar]
    survey_name = args.survey_name or questions_path.stem

    safe_scholar = args.scholar.replace(" ", "_")
    safe_model = MODEL_NAME.replace(".", "_")
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

                    prompt = build_prompt(
                        args.religion,
                        args.scholar,
                        variant["question"],
                        variant["coding"]
                    )

                    raw_answer = ask_model(vector_store_id, prompt)
                    numeric_answer = extract_number(raw_answer)

                    writer.writerow([
                        survey_name,
                        args.scholar,
                        args.religion,
                        MODEL_NAME,
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
                        f"survey={survey_name} "
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
