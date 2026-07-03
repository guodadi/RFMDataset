"""Backward-compatible entry point for RFMDataset evaluation."""

from rfmdataset.evaluation import (
    ERROR_CATEGORIES,
    ProofEvaluator,
    Proof_Evaluator,
    calc_accuracy,
    main,
    parse_proof_evaluation,
)

__all__ = [
    "ERROR_CATEGORIES",
    "ProofEvaluator",
    "Proof_Evaluator",
    "calc_accuracy",
    "main",
    "parse_proof_evaluation",
]


if __name__ == "__main__":
    main()
