#!/usr/bin/env python3
"""Import supplied Tong Standard Model solutions from a committed source tree."""

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_REPOSITORY = "https://github.com/Luca-Yucheng-Jin/QFT-soln"
PROBLEM = re.compile(r"\\subsection\{Sheet (\d+), Problem (\d+)\*?:[^}]*\}")
SOLUTION = re.compile(r"\\begin\{solution\}(.*?)\\end\{solution\}", re.S)
SHEETS = [
    {"sheet": 1, "title": "The Basics", "publishedProblems": [1, 2, 3, 4, 6, 7, 8],
     "excludedUnanswered": [5], "description": "Weyl spinors, fermion masses, and discrete symmetries."},
    {"sheet": 2, "title": "Symmetry Breaking and QCD", "publishedProblems": list(range(1, 9)),
     "excludedUnanswered": [9], "description": "Goldstone modes, Higgs mechanisms, QCD running, and meson masses."},
    {"sheet": 3, "title": "Anomalies", "publishedProblems": list(range(1, 7)),
     "excludedUnanswered": [], "description": "Gauge anomalies, hypercharges, anomaly matching, and global symmetries."},
    {"sheet": 4, "title": "The Standard Model", "publishedProblems": [1, 2, 4, 5, 6],
     "excludedUnanswered": [3, 7], "description": "Running couplings, electric charges, flavour parameters, and two Higgs doublets."},
]


def publication_formatting(block, sheet, number):
    block = block.replace("\\textquotesingle ", "'").replace(r"\textquotesingle", "'")
    # Repair the prematurely closed list in the supplied spinor solution.
    if (sheet, number) == (1, 2):
        block = block.replace("    \\end{enumerate}\n", "", 1)
        block = block.replace(r"\end{solution}", "    \\end{enumerate}\n\\end{solution}", 1)
    # Use representation names in both editions; MathJax lacks youngtab.
    block = block.replace(r"\yng(1,1)", r"\mathrm{antisym}")
    block = block.replace(r"\yng(2)", r"\mathrm{sym}")
    block = block.replace(r"\yng(1)", r"\mathrm{fund}")
    if sheet == 4:
        block = block.replace(r"\eqref{eq:LandauPole}",
            r"the one-loop relation in \href{https://luca-yucheng-jin.github.io/luca-physics-site/notes/tong-sm-sheet-2.html#sheet-2-problem-5-one-loop-qcd-scale}{Sheet 2, Problem 5}")
    return block


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--revision", default="origin/main")
    args = parser.parse_args()
    def git(*arguments):
        return subprocess.check_output(["git", *arguments], cwd=args.source, text=True)
    commit = git("rev-parse", args.revision).strip()
    entries = []
    for spec in SHEETS:
        sheet = spec["sheet"]
        source_path = f"sections/DTSMSheet{sheet}.tex"
        source = git("show", f"{commit}:{source_path}")
        matches = list(PROBLEM.finditer(source))
        preamble = source[:matches[0].start()]
        # The standalone edition has its own title and needs no manual line break.
        preamble = re.sub(r"\\section(?:\[[^]]*\])?\{.*?\}",
            lambda _: f"\\section{{David Tong The Standard Model, Sheet {sheet}: {spec['title']}}}",
            preamble, count=1, flags=re.S)
        chunks = [preamble]
        found = []
        solution_count = 0
        for index, match in enumerate(matches):
            number = int(match.group(2))
            if number not in spec["publishedProblems"]:
                continue
            end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
            block = source[match.start():end]
            bodies = SOLUTION.findall(block)
            if not bodies or any(not body.strip() or re.search(r"\bTODO\b|\bTBD\b|solutionplaceholder", body) for body in bodies):
                raise ValueError(f"Sheet {sheet}, Problem {number}: missing answer")
            chunks.append(publication_formatting(block, sheet, number).rstrip() + "\n\n")
            found.append(number)
            solution_count += len(bodies)
        if found != spec["publishedProblems"]:
            raise ValueError(f"Sheet {sheet}: source problem numbers changed")
        slug = f"tong-sm-sheet-{sheet}"
        tex_file = f"{slug}.tex"
        text = f"% Imported from {SOURCE_REPOSITORY}\n% Source commit: {commit}\n" + "".join(chunks)
        (ROOT / "tex" / tex_file).write_text("\n".join(line.rstrip() for line in text.splitlines()) + "\n")
        entries.append({**spec, "slug": slug, "texFile": tex_file, "sourcePath": source_path,
                        "problemCount": len(found), "solutionCount": solution_count})
    (ROOT / "assets" / "tong-sm-manifest.json").write_text(json.dumps(
        {"sourceRepository": SOURCE_REPOSITORY, "sourceCommit": commit, "sheets": entries}, indent=2) + "\n")
    print(f"Imported {sum(entry['problemCount'] for entry in entries)} worked problems in four sheets from {commit}.")


if __name__ == "__main__":
    main()
