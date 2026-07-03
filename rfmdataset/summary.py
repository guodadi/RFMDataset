"""Summary utilities for data and published results."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from .data import KNOWLEDGE_LEVELS, load_problems, read_json
from .evaluation import calc_accuracy, parse_proof_evaluation


def dataset_summary(data_dir: str | Path = "data") -> dict[str, object]:
    problems = load_problems(data_dir)
    by_level = {level: len(items) for level, items in problems.items()}
    by_subject: Counter[str] = Counter()
    by_difficulty: Counter[int] = Counter()

    for items in problems.values():
        for item in items:
            by_difficulty[int(item["level"])] += 1
            for category in item.get("categories", []):
                primary = category.get("primary")
                if primary:
                    by_subject[primary] += 1

    return {
        "total": sum(by_level.values()),
        "by_level": by_level,
        "by_subject": dict(by_subject.most_common()),
        "by_difficulty": dict(sorted(by_difficulty.items())),
    }


def judgement_accuracy(path: str | Path) -> dict[str, float]:
    judgements = read_json(path)
    labels = {
        level: [parse_proof_evaluation(item) for item in judgements[level]]
        for level in KNOWLEDGE_LEVELS
    }
    return calc_accuracy(labels)
