import json
import argparse
from scrubber import process_entry


def main():
    parser = argparse.ArgumentParser(description="PII Scrubber CLI")
    parser.add_argument(
        "--in",
        dest="input",
        required=True,
        help="Path to input JSONL file"
    )
    parser.add_argument(
        "--out",
        dest="output",
        required=True,
        help="Path to output JSONL file"
    )

    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as fin, \
         open(args.output, "w", encoding="utf-8") as fout:

        for line in fin:
            if not line.strip():
                continue

            entry = json.loads(line)
            result = process_entry(entry)
            fout.write(json.dumps(result, ensure_ascii=False) + "\n")

    print(f"✅ Scrubbing completed. Output written to: {args.output}")


if __name__ == "__main__":
    main()
