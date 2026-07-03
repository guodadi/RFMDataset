# RFMDataset

## Background
Large reasoning models (e.g., R1, o3) have demonstrated remarkable mathematical problem-solving abilities. However, the high reported accuracy of these advanced models on popular datasets, reliance on purely numerical evaluation and potential benchmark leakage, often masks their true reasoning shortcomings. To address this, we propose leveraging the inherent rigor and methodological complexity of mathematical proofs as a diagnostic tool to expose these hidden failures. Specifically, we introduce the RFMDataset (Reveal Failure Modes), a collection of 200 diverse mathematical proof problems, and thoroughly evaluate advanced models' performance on it. Our in-depth analysis of their failures uncovers 10 fine-grained error types, which shows fundamental limitations in current large reasoning models: 1) large reasoning models grapple profoundly with mathematical proofs, with some generating entirely correct proofs for less than 20\% of problems and failing even on basic ones; 2) models exhibit a diverse spectrum of reasoning failures, prominently demonstrating the lack of guarantees for the correctness and rigor of single-step reasoning; and 3) models show hallucination and incompleteness during the reasoning process. Our findings reveal that models' self-reflection is insufficient to resolve the current logical dilemmas, necessitating formalized and fine-grained logical training.

## RFMDataset
Our dataset contains 200 selected problems from an initial pool exceeding 1000 problems. The problems are stratified by knowledge level, encompassing junior high school (52 problems), senior high school (88 problems), and undergraduate curricula (60 problems). Furthermore, the dataset covers nine distinct mathematical subjects, including but not limited to geometry, trigonometry, number sequence, calculus, and probability. To assess nuanced reasoning capabilities, problems within each knowledge level are assigned one of four ascending difficulty levels (1 to 4) manually.
<img src="images/knowledge_distribution_new_00.jpg" alt="knowledge distribution" width="50%">
## Evaluation
Our LLM-as-a-judge method extends beyond holistic proof verification. We've developed a fine-grained error taxonomy comprising over 10 reasoning failure modes, including Logical Violation, Over Generalization, and Circular Reasoning. This enables the precise classification of model-generated proof failures, offering a deeper understanding of their shortcomings.
<img src="images/RFMDataset_00.jpg" alt="RFMDataset" width="90%">
## Notes
As our dataset contains some original questions, we will mark the sources of the questions in subsequent updates. We welcome everyone to point out the shortcomings in our work and thank all math enthusiasts for their sharing online.

## Repository Contents

- `data/`: the 200 proof problems grouped by knowledge level.
- `answers/`: published model answers.
- `judgements/`: published LLM-as-a-judge outputs.
- `prompt/`: prompts used for refinement and proof evaluation.
- `rfmdataset/`: reusable Python utilities for loading data, parsing judgements, and running evaluation.
- `scripts/`: command-line helpers built on top of `rfmdataset`.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

For development and tests:

```bash
pip install -r requirements-dev.txt
python -m unittest discover -s tests
```

## Quick Checks

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

The evaluation code uses OpenAI-compatible chat-completion APIs. Credentials are read only from environment variables; no API keys are stored in the repository. Copy `.env.example` to `.env` or export variables in your shell.

Example with the OpenAI API:

```bash
export OPENAI_API_KEY=...
python scripts/run_evaluation.py \
  --model o1 \
  --judge-model gpt-4.1 \
  --model-client openai \
  --judge-client openai \
  --answers-dir answers \
  --output-dir outputs/judgements
```

Example with a generic OpenAI-compatible gateway:

```bash
export OPENAI_COMPATIBLE_API_KEY=...
export OPENAI_COMPATIBLE_BASE_URL=https://your-endpoint.example/v1
python scripts/run_evaluation.py \
  --model your-model \
  --judge-model your-judge \
  --model-client openai-compatible \
  --judge-client openai-compatible
```

Generated outputs are written under `outputs/` by default and are intentionally ignored by Git.
