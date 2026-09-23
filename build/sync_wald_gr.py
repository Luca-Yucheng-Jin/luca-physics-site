#!/usr/bin/env python3
"""Import selected worked Wald exercises from a committed QFT-soln revision.

The source contains prompts for many exercises beyond the worked material.
Keep publication scoped to the reviewed parts of Chapters 3--6. The three
source references to earlier Tong GR work become links to the exact answers.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SITE = "https://luca-yucheng-jin.github.io/luca-physics-site"
SOURCE_REPOSITORY = "https://github.com/Luca-Yucheng-Jin/QFT-soln"
PROBLEM = re.compile(r"\\subsection\{Chapter (\d+), Problem (\d+):[^}]*\}")
SOLUTION = re.compile(r"\\begin\{solution\}(.*?)\\end\{solution\}", re.DOTALL)
ITEM = re.compile(r"(?m)^[ \t]*\\item\b")
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD|FIXME|unfinished|placeholder)\b", re.I)

CHAPTERS = [
    {
        "chapter": "3", "title": "Curvature", "slug": "wald-gr-chapter-3",
        "problemSolutions": {"1": 3, "2": 2, "3": 1, "4": 2, "5": 2, "6": 2},
        "publishedParts": {"3": ["b"]},
        "excludedIncomplete": ["3(a)", "7", "8"],
        "description": "Torsion, two-dimensional geometry, Riemann symmetries, curvature, affine parameters, and geodesics.",
    },
    {
        "chapter": "4", "title": "Einstein's Equation", "slug": "wald-gr-chapter-4",
        "problemSolutions": {"1": 1, "2": 2, "3": 3, "4": 1, "5": 1, "7": 2, "8": 1, "9": 1},
        "publishedParts": {"2": ["a", "b"]},
        "excludedIncomplete": ["2(c)", "6"],
        "description": "Maxwell theory, frame dragging, linearised gravity, and gravitational radiation.",
    },
    {
        "chapter": "5", "title": "Homogeneous, Isotropic Cosmology", "slug": "wald-gr-chapter-5",
        "problemSolutions": {"1": 1, "2": 1, "3": 2, "4": 3, "5": 3},
        "publishedParts": {}, "excludedIncomplete": [],
        "description": "Robertson-Walker coordinates, Friedmann equations, de Sitter spacetime, redshift, and null rays.",
    },
    {
        "chapter": "6", "title": "The Schwarzschild Solution", "slug": "wald-gr-chapter-6",
        "problemSolutions": {"1": 2, "3": 3, "4": 2, "5": 1, "6": 1},
        "publishedParts": {}, "publishedDrafts": ["5"], "excludedIncomplete": ["2"],
        "description": "Isotropic coordinates, Reissner-Nordström, stationary observers, a draft time-delay calculation, and horizon crossing.",
    },
]

TONG_LINKS = {
    ("3", "3"): (
        "See my worked solution to David Tong GR Problem Sheet 2, Question 8",
        f"{SITE}/notes/tong-gr-ps2.html#independent-components-of-the-riemann-tensor-q8",
    ),
    ("4", "4"): (
        "See my worked solution to David Tong GR Problem Sheet 4, Question 4",
        f"{SITE}/notes/tong-gr-ps4.html#the-fierz-pauli-action-q4-health-warning-this-question-is-not-short",
    ),
    ("4", "9"): (
        "See my related worked solution to David Tong GR Problem Sheet 4, Question 6",
        f"{SITE}/notes/tong-gr-ps4.html#gravitational-wave-emission-from-a-binary-system-q6",
    ),
}


def git_text(source: Path, revision: str, relative: str) -> str:
    return subprocess.run(
        ["git", "show", f"{revision}:{relative}"], cwd=source,
        check=True, capture_output=True, text=True,
    ).stdout


def keep_items(block: str, positions: tuple[int, ...]) -> str:
    """Retain only selected top-level items of one reviewed enumerate."""
    items = list(ITEM.finditer(block))
    if len(items) < max(positions):
        raise ValueError("Expected source item is missing")
    closing = block.rfind(r"\end{enumerate}")
    if closing < items[-1].end():
        raise ValueError("Expected enumerate end is missing")
    body = block[:items[0].start()]
    for position in positions:
        start = items[position - 1].start()
        end = items[position].start() if position < len(items) else closing
        body += block[start:end]
    return body + block[closing:]


def selected_chapter(text: str, chapter: dict) -> tuple[str, int]:
    matches = list(PROBLEM.finditer(text))
    if not matches:
        raise ValueError(f"No problems found in Chapter {chapter['chapter']}")
    expected_numbers = set(chapter["problemSolutions"])
    found = set()
    chunks = [text[:matches[0].start()]]
    solution_total = 0
    for index, match in enumerate(matches):
        if match.group(1) != chapter["chapter"]:
            raise ValueError("Unexpected chapter heading in source")
        number = match.group(2)
        if number not in expected_numbers:
            continue
        found.add(number)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.start():end]
        if (chapter["chapter"], number) == ("3", "3"):
            block = keep_items(block, (2,))
        elif (chapter["chapter"], number) == ("4", "2"):
            block = keep_items(block, (1, 2))
        elif (chapter["chapter"], number) == ("6", "5"):
            block = block.replace(
                r"\begin{solution}",
                r"\emph{Draft solution: the derivation below does not yet display the final time-delay formula (6.3.45).}"
                "\n" + r"\begin{solution}",
                1,
            )
        bodies = SOLUTION.findall(block)
        expected_count = chapter["problemSolutions"][number]
        if len(bodies) != expected_count:
            raise ValueError(f"Chapter {chapter['chapter']} Problem {number}: expected {expected_count} worked parts, found {len(bodies)}")
        for body in bodies:
            if not re.sub(r"[^A-Za-z0-9]", "", body) or PLACEHOLDER.search(body):
                raise ValueError(f"Chapter {chapter['chapter']} Problem {number}: incomplete solution")
        if (chapter["chapter"], number) in TONG_LINKS:
            label, url = TONG_LINKS[(chapter["chapter"], number)]
            if len(bodies) != 1 or not re.fullmatch(r"\s*See D\. Tong GR, PS\d(?:,?\s*Q\d)?\.?\s*\([^)]*\)\s*", bodies[0]):
                raise ValueError(f"Chapter {chapter['chapter']} Problem {number}: Tong reference changed")
            block = SOLUTION.sub(
                lambda _match: "\\begin{solution}\n" + f"\\href{{{url}}}{{{label}}}." + "\n\\end{solution}",
                block, count=1,
            )
        chunks.append(block.rstrip() + "\n\n")
        solution_total += len(bodies)
    if found != expected_numbers:
        raise ValueError(f"Chapter {chapter['chapter']}: reviewed problems changed: {found ^ expected_numbers}")
    return "".join(chunks).rstrip() + "\n", solution_total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--revision", default="origin/main")
    args = parser.parse_args()
    source = args.source.resolve()
    commit = subprocess.run(
        ["git", "rev-parse", args.revision], cwd=source,
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    chapters = []
    for spec in CHAPTERS:
        relative = f"sections/WaldGRCh{int(spec['chapter']):02d}.tex"
        source_text = git_text(source, args.revision, relative)
        if spec["chapter"] == "5":
            # The source's optional PDF running title is not understood by
            # the site's whole-file renderer; retain its full visible title.
            source_text = re.sub(
                r"\\section\[[^]]*\]\{[^}]*\}",
                lambda _match: r"\section{Wald General Relativity, Chapter 5: Homogeneous, Isotropic Cosmology}",
                source_text,
                count=1,
            )
        text, count = selected_chapter(source_text, spec)
        text = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
        tex_file = f"{spec['slug']}.tex"
        (ROOT / "tex" / tex_file).write_text(
            "% Generated from selected worked problems in committed QFT-soln sources.\n"
            f"% Source repository: {SOURCE_REPOSITORY}\n"
            f"% Source commit: {commit}\n" + text,
            encoding="utf-8",
        )
        chapters.append({
            **{key: value for key, value in spec.items() if key != "problemSolutions"},
            "sourcePath": relative, "texFile": tex_file,
            "publishedProblems": list(spec["problemSolutions"]),
            "solutionCount": count,
        })
    manifest = {
        "sourceRepository": SOURCE_REPOSITORY,
        "sourceCommit": commit,
        "chapters": chapters,
    }
    (ROOT / "assets" / "wald-gr-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )
    print(f"Imported {len(chapters)} Wald chapters with {sum(c['solutionCount'] for c in chapters)} worked or linked parts from {commit}.")


if __name__ == "__main__":
    main()
