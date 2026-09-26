#!/usr/bin/env python3
"""Import reviewed, worked Tong Statistical Field Theory problems from QFT-soln."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SOURCE_REPOSITORY = "https://github.com/Luca-Yucheng-Jin/QFT-soln"
PROBLEM = re.compile(r"\\subsection\{Sheet (\d+), Problem (\d+)\*?:[^}]*\}")
SOLUTION = re.compile(r"\\begin\{solution\}(.*?)\\end\{solution\}", re.DOTALL)
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|FIXME|not repeat)\b", re.I)

SHEETS = [
    {
        "sheet": 1, "title": "Landau Theory", "slug": "tong-sft-sheet-1",
        "publishedProblems": [1, 3, 6, 8],
        "excludedIncomplete": [2, 4, 5, 7],
        "description": "Transfer matrices, exact mean-field theory, spin order, and scaling.",
    },
    {
        "sheet": 2, "title": "Correlations and Scaling", "slug": "tong-sft-sheet-2",
        "publishedProblems": [1, 5, 7],
        "excludedIncomplete": [2, 3, 4, 6, 8],
        "description": "Ornstein-Zernike correlations, Lifshitz scaling, and anisotropy.",
    },
    {
        "sheet": 3, "title": "Renormalisation Group", "slug": "tong-sft-sheet-3",
        "publishedProblems": [1, 2, 3, 4, 5, 6],
        "excludedIncomplete": [],
        "description": "Critical exponents, fixed-point flows, sine-Gordon theory, and membranes.",
    },
]


def git_show(source: Path, revision: str, relative: str) -> bytes:
    return subprocess.run(
        ["git", "show", f"{revision}:{relative}"], cwd=source,
        check=True, capture_output=True,
    ).stdout


def selected_sheet(source_text: str, spec: dict) -> tuple[str, int]:
    matches = list(PROBLEM.finditer(source_text))
    if not matches:
        raise ValueError(f"No problems found in Sheet {spec['sheet']}")
    chosen = set(spec["publishedProblems"])
    found: set[int] = set()
    chunks = [source_text[:matches[0].start()]]
    for index, match in enumerate(matches):
        sheet, number = map(int, match.groups())
        if sheet != spec["sheet"]:
            raise ValueError("Unexpected sheet number in source")
        if number not in chosen:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source_text)
        block = source_text[match.start():end]
        bodies = SOLUTION.findall(block)
        if len(bodies) != 1 or len(bodies[0].strip()) < 100 or PLACEHOLDER.search(bodies[0]):
            raise ValueError(f"Sheet {sheet}, Problem {number}: incomplete solution")
        found.add(number)
        chunks.append(block.rstrip() + "\n\n")
    if found != chosen:
        raise ValueError(f"Sheet {spec['sheet']}: reviewed problems changed: {found ^ chosen}")
    return "".join(chunks).rstrip() + "\n", len(found)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--revision", default="origin/main")
    args = parser.parse_args()
    source = args.source.resolve()
    commit = subprocess.run(
        ["git", "rev-parse", args.revision], cwd=source,
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    sheets = []
    for spec in SHEETS:
        relative = f"sections/DTSFTSheet{spec['sheet']}.tex"
        imported, count = selected_sheet(git_show(source, args.revision, relative).decode(), spec)
        if spec["sheet"] == 3:
            # Correct narrowly identified transcription slips in the public
            # copy; do not modify the author's source checkout.
            corrections = [
                (r"\cos(\beta_0(\phi^-+\phi^+) + \mathcal{O}(\lambda_0^2)\right)",
                 r"\cos(\beta_0(\phi^-+\phi^+)) + \mathcal{O}(\lambda_0^2)\right)"),
                (r"\frac{1}{2i}\left[\left\langle", r"\frac{1}{2}\left[\left\langle"),
                (r"\right\rangle_+e^{\beta_0\phi^-}", r"\right\rangle_+e^{i\beta_0\phi^-}"),
                (r"\right\rangle_+e^{-\beta_0\phi^-}", r"\right\rangle_+e^{-i\beta_0\phi^-}"),
                (r"\lambda_2 = \epsilon", r"\lambda_2 = -\epsilon"),
                (r"\frac{N+2}{2\pi^2}\left(1+\frac{1}{2}\frac{N+2}{N+8}\right)\Lambda",
                 r"\frac{N+2}{2\pi^2}\left(1+\frac{1}{2}\frac{N+2}{N+8}\epsilon\right)\Lambda^2"),
                ("\\beta = \\nu \\Delta_\\phi = \n\\beta\n=", r"\beta = \nu \Delta_\phi ="),
                ("=\n\\gamma\n=", "="),
                (r"the red line denotes $\phi_+$", r"the red line denotes $\phi_2$"),
            ]
            for old, new in corrections:
                if imported.count(old) != 1:
                    raise ValueError(f"Sheet 3 reviewed expression changed: {old}")
                imported = imported.replace(old, new)
        imported = "\n".join(line.rstrip() for line in imported.splitlines()) + "\n"
        tex_file = f"{spec['slug']}.tex"
        (ROOT / "tex" / tex_file).write_text(
            "% Generated from selected worked problems in committed QFT-soln sources.\n"
            f"% Source repository: {SOURCE_REPOSITORY}\n"
            f"% Source commit: {commit}\n" + imported,
            encoding="utf-8",
        )
        sheets.append({**spec, "sourcePath": relative, "texFile": tex_file, "solutionCount": count})
    figure = "fig/cubic-rg-flow.png"
    figure_path = ROOT / "assets" / figure
    figure_path.parent.mkdir(parents=True, exist_ok=True)
    figure_path.write_bytes(git_show(source, args.revision, figure))
    (ROOT / "assets" / "tong-sft-manifest.json").write_text(
        json.dumps({"sourceRepository": SOURCE_REPOSITORY, "sourceCommit": commit, "sheets": sheets},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Imported {len(sheets)} SFT sheets with {sum(sheet['solutionCount'] for sheet in sheets)} worked problems from {commit}.")


if __name__ == "__main__":
    main()
