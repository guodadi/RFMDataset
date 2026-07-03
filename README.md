# RFMDataset

RFMDataset (Reveal Failure Modes) is a benchmark for evaluating mathematical proof reasoning in large reasoning models. It contains 200 proof problems, published model answers, LLM-as-a-judge outputs, prompts, and reusable code for loading the data and reproducing the evaluation workflow.

This is the official repository for the paper "Mathematical Proof as a Litmus Test: Revealing Failure Modes of Advanced Large Reasoning Models".

## Overview

Large reasoning models (for example, R1 and o3) have shown strong mathematical problem-solving ability on many popular benchmarks. However, aggregate accuracy on numerical-answer datasets can hide deeper issues such as benchmark leakage, incomplete reasoning, hallucinated proof steps, and invalid local deductions.

RFMDataset uses mathematical proofs as a diagnostic setting. The benchmark focuses on fine-grained failure analysis rather than only final-answer correctness. Our evaluation identifies more than 10 reasoning error patterns, including Logical Violation, Over Generalization, Circular Reasoning, Hidden Assumption, Vague Argument, and Incomplete Proof.

## Dataset

RFMDataset contains 200 selected proof problems from an initial pool of more than 1000 problems. The released problems are stratified by knowledge level:

| Level | Count |
| --- | ---: |
| Junior high school (`ms`) | 52 |
| Senior high school (`hs`) | 88 |
| Undergraduate (`ug`) | 60 |

The dataset covers nine mathematical subjects, including geometry, trigonometry, number sequence, calculus, probability, algebra, set theory, number theory, and combinatorics. Each problem is manually assigned one of four difficulty levels.

<img src="images/knowledge_distribution_new_00.jpg" alt="knowledge distribution" width="50%">

## Evaluation

The evaluation method uses an LLM-as-a-judge prompt that goes beyond holistic proof verification. For each proof, the judge produces a binary label for each error pattern and an overall correctness label.

<img src="images/RFMDataset_00.jpg" alt="RFMDataset" width="90%">

The expected judgement block has the following structure:

```markdown
### Error Pattern Analysis
- Transformation Error: 1|0
- Over Generalization: 1|0
- Invalid Construction: 1|0
- Wrong Division: 1|0
- Circular Reasoning: 1|0
- Logic Violation: 1|0
- Hidden Assumption: 1|0
- Boundary Neglect: 1|0
- Vague Argument: 1|0
- Incomplete Proof: 1|0
- Others: 1|0

### Overall Correctness
- 1|0
```

## Experimental Results

The main evaluation shows that even advanced reasoning models still struggle with proof generation in RFMDataset. The highlighted cells indicate the strongest results within each column.

<img src="images/rfm_main_results_table.png" alt="main RFMDataset accuracy results" width="90%">

The failure-mode analysis shows that models frequently suffer from logical violations, incomplete proofs, vague arguments, and hidden assumptions. The right heatmap reports model accuracy across mathematical domains.

<img src="images/rfm_error_patterns.png" alt="RFMDataset error pattern and domain analysis" width="95%">

We also evaluate model-specific self-reflection prompts. Reflection can improve selected models on some subsets, but the gains are not uniform across models or difficulty levels.

<img src="images/rfm_reflection_results_table.png" alt="self-reflection results on RFMDataset" width="90%">

## Repository Contents

| Path | Description |
| --- | --- |
| `data/` | The 200 proof problems grouped by knowledge level. |
| `answers/` | Published model answers used in the evaluation. |
| `judgements/` | Published LLM-as-a-judge outputs. |
| `prompt/` | Prompts used for proof evaluation and refinement. |
| `images/` | Figures used in this README and the paper. |
| `rfmdataset/` | Reusable Python package for loading data, parsing judgements, and running evaluation. |
| `scripts/` | Command-line helpers built on top of `rfmdataset`. |
| `tests/` | Lightweight tests for data loading and evaluation parsing. |

## Installation

Use Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

For development checks:

```bash
pip install -r requirements-dev.txt
python -m unittest discover -s tests
```

## Quick Start

Print dataset statistics:

```bash
python scripts/summarize_dataset.py
```

Compute accuracy from an existing judgement file:

```bash
python scripts/summarize_judgements.py judgements/o1_gemini-2.5-pro-preview-0506_all.json
```

Parse a LaTeX source file whose problems are written as `\section*{Question ...}` blocks:

```bash
python scripts/parse_latex.py raw.tex -o problems.json
```

## Running LLM-as-a-Judge Evaluation

The evaluation code calls OpenAI-compatible chat-completion APIs. The repository intentionally does not provide API keys, vendor presets, or default endpoint URLs. Users must provide both the API key and the base URL.

Set the default environment variables:

```bash
export RFM_MODEL_API_KEY=...
export RFM_MODEL_BASE_URL=https://your-model-endpoint.example/v1
export RFM_JUDGE_API_KEY=...
export RFM_JUDGE_BASE_URL=https://your-judge-endpoint.example/v1
```

Then run evaluation on a published answer file:

```bash
python scripts/run_evaluation.py \
  --model your-model \
  --judge-model your-judge \
  --answers-dir answers \
  --output-dir outputs/judgements
```

If you prefer different environment variable names, pass them explicitly:

```bash
export MY_MODEL_KEY=...
export MY_MODEL_URL=https://your-model-endpoint.example/v1
export MY_JUDGE_KEY=...
export MY_JUDGE_URL=https://your-judge-endpoint.example/v1

python scripts/run_evaluation.py \
  --model your-model \
  --judge-model your-judge \
  --model-api-key-env MY_MODEL_KEY \
  --model-base-url-env MY_MODEL_URL \
  --judge-api-key-env MY_JUDGE_KEY \
  --judge-base-url-env MY_JUDGE_URL
```

Generated files are written under `outputs/` by default and are ignored by Git.

## Python Usage

```python
from rfmdataset import __version__
from rfmdataset.data import load_problems
from rfmdataset.summary import dataset_summary, judgement_accuracy

problems = load_problems("data")
print(dataset_summary("data"))
print(judgement_accuracy("judgements/o1_gemini-2.5-pro-preview-0506_all.json"))
```

## Notes

Some problems are original. We will continue to mark and refine problem sources in subsequent updates. We welcome feedback and issue reports.

## License

This repository is released under the MIT License. See [LICENSE](LICENSE).
