"""Evaluation parsing and LLM-as-judge runner for RFMDataset."""

from __future__ import annotations

import argparse
import re
import time
from pathlib import Path
from typing import Any

from tqdm import tqdm

from .data import KNOWLEDGE_LEVELS, load_answers, load_problem_statements, read_json, repo_root, write_json
from .llm import GPTChatter

ERROR_CATEGORIES = (
    "Transformation Error",
    "Over Generalization",
    "Invalid Construction",
    "Wrong Division",
    "Circular Reasoning",
    "Logic Violation",
    "Hidden Assumption",
    "Boundary Neglect",
    "Vague Argument",
    "Incomplete Proof",
    "Others",
)


def parse_proof_evaluation(text: str) -> dict[str, int] | None:
    """Parse the rubric block emitted by the judge prompt.

    Returns None when the response does not contain the expected sections.
    """

    if not isinstance(text, str):
        return None
    if "### Error Pattern Analysis" not in text or "### Overall Correctness" not in text:
        return None

    result: dict[str, int] = {}
    for category in ERROR_CATEGORIES:
        match = re.search(rf"{re.escape(category)}:\s*([01])", text, flags=re.IGNORECASE)
        result[category] = int(match.group(1)) if match else 0

    overall = re.search(
        r"Overall\s+Correctness\s*[\n\r\s\-:]*([01])",
        text,
        flags=re.IGNORECASE,
    )
    result["Overall Correctness"] = (
        int(overall.group(1)) if overall else int(all(value == 0 for value in result.values()))
    )
    return result


def strip_thinking(answer: str) -> str:
    """Return the final answer after a </think> tag when present."""

    if "</think>" not in answer:
        return answer
    thought, proof = answer.split("</think>", maxsplit=1)
    proof = proof.strip()
    if len(proof.split()) < 10:
        return thought.removeprefix("<think>").strip()
    return proof


def calc_accuracy(labels: dict[str, list[dict[str, Any] | None]]) -> dict[str, float]:
    """Compute per-level and overall correctness from parsed labels."""

    accuracy: dict[str, float] = {}
    total_correct = 0
    total_count = 0
    for level, records in labels.items():
        if not records:
            accuracy[level] = 0.0
            continue
        correct = sum(1 for record in records if record and record.get("Overall Correctness") == 1)
        accuracy[level] = correct / len(records)
        total_correct += correct
        total_count += len(records)
    accuracy["overall"] = total_correct / total_count if total_count else 0.0
    return accuracy


class ProofEvaluator:
    """Generate answers, judge proofs, and parse judge outputs."""

    def __init__(
        self,
        model_name: str,
        judge_model_name: str,
        *,
        model_client: str = "openai",
        judge_client: str = "openai",
        project_root: str | Path | None = None,
    ) -> None:
        self.root = Path(project_root) if project_root else repo_root()
        self.model_name = model_name
        self.judge_model_name = judge_model_name
        self.questions = load_problem_statements(self.root / "data")
        self.model_client = GPTChatter(model_name=model_name, client=model_client)
        self.judge_model_client = GPTChatter(model_name=judge_model_name, client=judge_client)

    def generate_answers(self, *, batch_size: int = 1, output_dir: str | Path | None = None) -> Path:
        answers: dict[str, list[str]] = {}
        for level in KNOWLEDGE_LEVELS:
            level_answers: list[str] = []
            questions = self.questions[level]
            for index in tqdm(range(0, len(questions), batch_size), desc=f"Answering {level}"):
                batch = questions[index : index + batch_size]
                level_answers.extend(self.model_client.get_llm_response(batch))
            answers[level] = level_answers

        target_dir = Path(output_dir) if output_dir else self.root / "outputs" / "answers"
        output_path = target_dir / f"{self.model_name}_all.json"
        write_json(answers, output_path)
        return output_path

    def evaluate_answers(
        self,
        *,
        answers_dir: str | Path | None = None,
        output_dir: str | Path | None = None,
        batch_size: int = 16,
        max_retries: int = 3,
        retry_delay: float = 5.0,
        strip_think: bool = True,
    ) -> Path:
        answers = load_answers(self.model_name, answers_dir or self.root / "answers")
        prompt_template = (self.root / "prompt" / "eval_prompt.txt").read_text(encoding="utf-8")

        target_dir = Path(output_dir) if output_dir else self.root / "outputs" / "judgements"
        output_path = target_dir / f"{self.model_name}_{self.judge_model_name}_all.json"
        judgements = read_json(output_path) if output_path.exists() else {}

        for level in KNOWLEDGE_LEVELS:
            existing = judgements.get(level, [])
            level_answers = answers[level]
            if len(existing) < len(level_answers):
                existing.extend([None] * (len(level_answers) - len(existing)))
            judgements[level] = existing

            pending = [
                {"index": idx, "question": self.questions[level][idx], "answer": answer}
                for idx, answer in enumerate(level_answers)
                if existing[idx] is None
                or (isinstance(existing[idx], str) and existing[idx].lower().startswith("error"))
            ]

            for start in tqdm(range(0, len(pending), batch_size), desc=f"Judging {level}"):
                batch = pending[start : start + batch_size]
                remaining = batch
                successful: dict[int, str] = {}

                for attempt in range(max_retries):
                    prompts = [
                        prompt_template.format(
                            Question=item["question"],
                            Proof=strip_thinking(item["answer"]) if strip_think else item["answer"],
                        )
                        for item in remaining
                    ]
                    responses = self.judge_model_client.get_llm_response(prompts)
                    next_remaining = []
                    for item, response in zip(remaining, responses):
                        if response.strip().lower().startswith("error"):
                            next_remaining.append(item)
                        else:
                            successful[item["index"]] = response
                    remaining = next_remaining
                    if not remaining:
                        break
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)

                for index, response in successful.items():
                    judgements[level][index] = response
                for item in remaining:
                    judgements[level][item["index"]] = f"Error: Failed after {max_retries} retries."
                write_json(judgements, output_path)

        return output_path

    def parse_judgements(self, judgement_path: str | Path, output_path: str | Path | None = None) -> Path:
        judgements = read_json(judgement_path)
        labels = {
            level: [parse_proof_evaluation(item) for item in judgements[level]]
            for level in KNOWLEDGE_LEVELS
        }
        target = Path(output_path) if output_path else self.root / "outputs" / "labels" / Path(judgement_path).name
        write_json(labels, target)
        return target


# Backward-compatible class name used by the original scripts.
Proof_Evaluator = ProofEvaluator


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run RFMDataset LLM-as-judge evaluation.")
    parser.add_argument("--model", required=True, help="Model whose answers are evaluated.")
    parser.add_argument("--judge-model", required=True, help="Judge model name.")
    parser.add_argument("--model-client", default="openai", help="Client key from rfmdataset.llm.CLIENT_CONFIGS.")
    parser.add_argument("--judge-client", default="openai", help="Client key from rfmdataset.llm.CLIENT_CONFIGS.")
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--answers-dir", default="answers")
    parser.add_argument("--output-dir", default="outputs/judgements")
    args = parser.parse_args(argv)

    evaluator = ProofEvaluator(
        args.model,
        args.judge_model,
        model_client=args.model_client,
        judge_client=args.judge_client,
    )
    path = evaluator.evaluate_answers(
        answers_dir=args.answers_dir,
        output_dir=args.output_dir,
        batch_size=args.batch_size,
    )
    print(f"Saved judgements to {path}")


if __name__ == "__main__":
    main()
