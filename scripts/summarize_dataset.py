from __future__ import annotations

import argparse
import json

from _bootstrap import add_repo_root_to_path

add_repo_root_to_path()

from rfmdataset.summary import dataset_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Print RFMDataset problem statistics.")
    parser.add_argument("--data-dir", default="data")
    args = parser.parse_args()
    print(json.dumps(dataset_summary(args.data_dir), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
