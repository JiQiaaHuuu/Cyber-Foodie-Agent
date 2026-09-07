import json
from pathlib import Path


def main() -> None:
    evalset = json.loads(Path("eval/evalset.json").read_text(encoding="utf-8"))
    print(f"Loaded {len(evalset)} evaluation cases.")
    for case in evalset:
        print(f"{case['id']}: " + "；".join(case["expected"]))


if __name__ == "__main__":
    main()
