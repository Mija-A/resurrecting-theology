import argparse
import json
import subprocess
from pathlib import Path

MAP_FILE = Path("vector_stores.json")


def load_store_map():
    with open(MAP_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--religion", required=True)
    parser.add_argument("--questions", required=True)
    parser.add_argument("--survey-name", default="")
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--scholars", nargs="*", default=None)
    args = parser.parse_args()

    store_map = load_store_map()
    scholars = args.scholars if args.scholars else sorted(store_map.keys())

    for scholar in scholars:
        print(f"\n=== Running scholar: {scholar} ===\n")

        cmd = [
            "python3",
            "ask.py",
            "--scholar", scholar,
            "--religion", args.religion,
            "--questions", args.questions,
            "--rounds", str(args.rounds),
            "--seed", str(args.seed),
        ]

        if args.survey_name:
            cmd.extend(["--survey-name", args.survey_name])

        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()