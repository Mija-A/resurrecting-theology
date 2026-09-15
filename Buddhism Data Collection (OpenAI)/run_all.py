import json
import subprocess
import argparse
from pathlib import Path

MAP_FILE = Path("vector_stores.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--religion", required=True, help='Example: "Hindu"')
    parser.add_argument("--rounds", default="10")
    parser.add_argument("--questions", required=True, help="Question JSON file")
    parser.add_argument("--survey-name", default="", help="Optional survey label")

    args = parser.parse_args()

    if not MAP_FILE.exists():
        raise FileNotFoundError("vector_stores.json not found. Run upload_docs.py first.")

    with open(MAP_FILE, "r", encoding="utf-8") as f:
        store_map = json.load(f)

    for scholar in store_map:
        print("\n====================")
        print("Running:", scholar)
        print("====================\n")

        cmd = [
            "python3",
            "ask.py",
            "--scholar", scholar,
            "--religion", args.religion,
            "--rounds", str(args.rounds),
            "--questions", args.questions,
        ]

        if args.survey_name:
            cmd.extend(["--survey-name", args.survey_name])

        result = subprocess.run(cmd)

        if result.returncode != 0:
            print(f"\nStopped because ask.py failed for: {scholar}")
            break


if __name__ == "__main__":
    main()