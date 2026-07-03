"""Parse RFMDataset-style LaTeX question files into JSON."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

SECTION_RE = re.compile(r"\\section\*\{(Question[^}]*)\}", re.S)


def parse_header(header: str) -> dict[str, Any]:
    match = re.search(
        r"Question\s+(\d+)\s*\(\s*(?:level|Level)\s+(\d+)\s*\)",
        header,
        flags=re.I,
    )
    if not match:
        raise ValueError(f"Cannot parse question id and level from header: {header!r}")
    question_id, level = match.groups()

    raw_groups = re.findall(r"\(([^()]*)\)", header)[1:]
    categories = []
    for group in raw_groups:
        if ";" in group or ":" in group:
            primary, secondary = re.split(r"[;:]", group, 1)
            category = {
                "primary": primary.strip(),
                "secondary": [item.strip() for item in secondary.split(",") if item.strip()],
            }
        else:
            category = {"primary": group.strip()}
        categories.append(category)

    return {"id": question_id, "level": int(level), "categories": categories}


def parse_tex(tex: str) -> list[dict[str, Any]]:
    problems = []
    sections = list(SECTION_RE.finditer(tex))
    for index, section in enumerate(sections):
        body_start = section.end()
        body_end = sections[index + 1].start() if index + 1 < len(sections) else len(tex)
        item = parse_header(section.group(1))
        item["statement"] = tex[body_start:body_end].strip()
        problems.append(item)
    return problems


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Convert LaTeX question sections to JSON.")
    parser.add_argument("input", type=Path, help="Input .tex file")
    parser.add_argument("-o", "--output", type=Path, default=Path("problems.json"))
    args = parser.parse_args(argv)

    problems = parse_tex(args.input.read_text(encoding="utf-8"))
    args.output.write_text(json.dumps(problems, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Parsed {len(problems)} problems to {args.output}")


if __name__ == "__main__":
    main()
