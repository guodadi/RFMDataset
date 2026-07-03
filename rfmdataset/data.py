"""Data loading helpers for the repository's published JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

KNOWLEDGE_LEVELS = ("ms", "hs", "ug")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def read_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8-sig") as file:
        return json.load(file)


def write_json(data: Any, path: str | Path, *, indent: int = 2) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=indent)


def load_problems(data_dir: str | Path | None = None) -> dict[str, list[dict[str, Any]]]:
    """Load the 200 RFMDataset proof problems grouped by knowledge level."""

    base = Path(data_dir) if data_dir is not None else repo_root() / "data"
    return {
        level: read_json(base / f"{level}_combined.json")
        for level in KNOWLEDGE_LEVELS
    }


def load_problem_statements(data_dir: str | Path | None = None) -> dict[str, list[str]]:
    return {
        level: [item["statement"] for item in items]
        for level, items in load_problems(data_dir).items()
    }


def load_answers(model_name: str, answers_dir: str | Path | None = None) -> dict[str, list[str]]:
    """Load published model answers from answers/{model_name}_all.json."""

    base = Path(answers_dir) if answers_dir is not None else repo_root() / "answers"
    return read_json(base / f"{model_name}_all.json")


def load_judgements(
    model_name: str,
    judge_model_name: str,
    judgements_dir: str | Path | None = None,
) -> dict[str, list[str]]:
    """Load published LLM-as-judge outputs for a model/judge pair."""

    base = Path(judgements_dir) if judgements_dir is not None else repo_root() / "judgements"
    return read_json(base / f"{model_name}_{judge_model_name}_all.json")
