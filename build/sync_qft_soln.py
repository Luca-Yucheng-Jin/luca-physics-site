#!/usr/bin/env python3
"""Import completed PSI QFT II sheets from the committed QFT-soln tree.

The importer reads with ``git show`` so local, uncommitted coursework cannot
leak onto the public site. Publication is deliberately allow-listed: every
sheet below has been checked for a complete set of substantive solution
blocks, while Tutorial 2 and Homework 3 remain unpublished.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_OUTPUT = ROOT / "assets" / "qft-soln-manifest.json"

PLACEHOLDER = re.compile(
    r"\b(?:TODO|TBD|unfinished)\b|placeholder|solution\s+to\s+be\s+written",
    re.IGNORECASE,
)
SOLUTION = re.compile(
    r"\\begin\{solution\}(.*?)\\end\{solution\}", re.DOTALL
)

SHEETS = [
    {
        "kind": "Homework",
        "number": "1",
        "slug": "psi-qft-ii-homework-1",
        "title": "Generating Functionals for φ⁴ Theory",
        "sourcePath": "sections/PSIQFTII_Homework1.tex",
        "solutionCount": 10,
        "description": "Generating functionals, connected correlators, vacuum diagrams, and the 1PI effective action.",
    },
    {
        "kind": "Homework",
        "number": "2",
        "slug": "psi-qft-ii-homework-2",
        "title": "Renormalization in Massive φ⁴ Theory",
        "sourcePath": "sections/PSIQFTII_Homework2.tex",
        "solutionCount": 15,
        "description": "Cutoff renormalization, running coupling and mass, and RG flow in the O(N) model.",
    },
    {
        "kind": "Tutorial",
        "number": "3",
        "slug": "psi-qft-ii-tutorial-3",
        "title": "Saddle-Point Approximation and Functional Determinants",
        "sourcePath": "sections/PSIQFTII_Tutorial3.tex",
        "solutionCount": 15,
        "description": "Saddle points, functional determinants, zeta regularization, and the Gel'fand-Yaglom formalism.",
    },
    {
        "kind": "Tutorial",
        "number": "4",
        "slug": "psi-qft-ii-tutorial-4",
        "title": "Exact Results in Quantum Field Theory",
        "sourcePath": "sections/PSIQFTII_Tutorial4.tex",
        "solutionCount": 16,
        "description": "The Källén-Lehmann representation, spectral functions, and Schwinger-Dyson equations.",
    },
    {
        "kind": "Tutorial",
        "number": "5",
        "slug": "psi-qft-ii-tutorial-5",
        "title": "Effective Action and Renormalization in φ³ Theory",
        "sourcePath": "sections/PSIQFTII_Tutorial5.tex",
        "solutionCount": 7,
        "description": "The effective action, loop expansion, counterterms, and renormalization of φ³ theory.",
    },
    {
        "kind": "Tutorial",
        "number": "6",
        "slug": "psi-qft-ii-tutorial-6",
        "title": "Renormalization-Group Flow in Three Dimensions",
        "sourcePath": "sections/PSIQFTII_Tutorial6.tex",
        "solutionCount": 7,
        "description": "Dimensionless couplings, beta functions, and the infrared fixed point of three-dimensional φ⁴ theory.",
    },
    {
        "kind": "Tutorial",
        "number": "7",
        "slug": "psi-qft-ii-tutorial-7",
        "title": "Berezin Integration and the Gross-Neveu Model",
        "sourcePath": "sections/PSIQFTII_Tutorial7.tex",
        "solutionCount": 10,
        "description": "Grassmann Gaussian integrals, fermionic correlators, and large-N Gross-Neveu theory.",
    },
    {
        "kind": "Tutorial",
        "number": "8",
        "slug": "psi-qft-ii-tutorial-8",
        "title": "SU(N) Yang-Mills Theory and Scalar Fields",
        "sourcePath": "sections/PSIQFTII_Tutorial8.tex",
        "solutionCount": 11,
        "description": "Fundamental and adjoint representations, covariant derivatives, scalar couplings, and Yang-Mills zero modes.",
    },
    {
        "kind": "Tutorial",
        "number": "9",
        "slug": "psi-qft-ii-tutorial-9",
        "title": "The Faddeev-Popov Determinant",
        "sourcePath": "sections/PSIQFTII_Tutorial9.tex",
        "solutionCount": 10,
        "description": "Gauge-orbit volume, gauge slices, Jacobians, Gaussian gauge fixing, and ghost variables.",
    },
]


def git_text(source: Path, revision: str, relative: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{revision}:{relative}"],
        cwd=source,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def validate_sheet(text: str, expected_count: int, relative: str) -> None:
    if PLACEHOLDER.search(text):
        raise SystemExit(f"Placeholder marker found in {relative}; refusing to publish.")
    bodies = SOLUTION.findall(text)
    if len(bodies) != expected_count:
        raise SystemExit(
            f"Expected {expected_count} solutions in {relative}, found {len(bodies)}; "
            "refusing to publish."
        )
    for index, body in enumerate(bodies, start=1):
        substantive = re.sub(r"[^A-Za-z0-9]+", "", body)
        if not substantive:
            raise SystemExit(
                f"Solution {index} in {relative} is empty or a stub; refusing to publish."
            )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--revision", default="origin/main")
    args = parser.parse_args()
    source = args.source.resolve()

    commit = subprocess.run(
        ["git", "rev-parse", args.revision],
        cwd=source,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    manifest_sheets = []
    for sheet in SHEETS:
        text = git_text(source, args.revision, sheet["sourcePath"])
        validate_sheet(text, sheet["solutionCount"], sheet["sourcePath"])
        # ``myblue`` is defined in the source repository's document-level
        # style file. The website renders each TikZ figure independently, so
        # use the identical explicit xcolor expression in the imported copy.
        text = text.replace("myblue", "blue!80!black")
        text = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
        tex_file = f"{sheet['slug']}.tex"
        imported = (
            "% Generated by build/sync_qft_soln.py from committed sources only.\n"
            "% Source repository: https://github.com/Luca-Yucheng-Jin/QFT-soln\n"
            f"% Source commit: {commit}\n"
            + text.rstrip()
            + "\n"
        )
        (ROOT / "tex" / tex_file).write_text(imported, encoding="utf-8")
        manifest_sheets.append({**sheet, "texFile": tex_file})

    manifest = {
        "sourceRepository": "https://github.com/Luca-Yucheng-Jin/QFT-soln",
        "sourceCommit": commit,
        "sheets": manifest_sheets,
        "excludedIncomplete": [
            "sections/PSIQFTII_Tutorial2.tex",
            "sections/PSIQFTII_Homework3.tex",
        ],
    }
    MANIFEST_OUTPUT.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        f"Imported {len(manifest_sheets)} completed PSI QFT II sheets "
        f"from {commit}."
    )


if __name__ == "__main__":
    main()
