from __future__ import annotations

import argparse
import json

from _bootstrap import add_repo_root_to_path

add_repo_root_to_path()

from rfmdataset.summary import judgement_accuracy


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute accuracy from a judgement JSON file.")
    parser.add_argument("path", help="Path to a judgements/*_all.json file")
    args = parser.parse_args()
    print(json.dumps(judgement_accuracy(args.path), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
