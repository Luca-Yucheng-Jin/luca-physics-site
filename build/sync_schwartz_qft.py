#!/usr/bin/env python3
"""Import only completed Schwartz QFT solutions from a Git checkout.

The importer reads committed files with ``git show <revision>:<path>`` so unfinished
or unrelated working-tree changes cannot leak into the public site.  A problem
is publishable only when it has a non-trivial solution body and no placeholder
marker.  Figures are rendered from the committed PDF assets to web PNGs.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TEX_OUTPUT = ROOT / "tex" / "schwartz-qft-solutions.tex"
MANIFEST_OUTPUT = ROOT / "assets" / "schwartz-qft-manifest.json"

PROBLEMS = {
    "29.1": {
        "path": "chapters/chapter_29/problems/29_1.tex",
        "title": "Higgs Production at LEP",
        "slug": "schwartz-qft-29-1",
    },
    "29.2": {
        "path": "chapters/chapter_29/problems/29_2.tex",
        "title": "Electron-Positron Annihilation into Hadrons",
        "slug": "schwartz-qft-29-2",
    },
    "29.3": {
        "path": "chapters/chapter_29/problems/29_3.tex",
        "title": "Higgs Decays",
        "slug": "schwartz-qft-29-3",
    },
    "29.4": {
        "path": "chapters/chapter_29/problems/29_4.tex",
        "title": "Partial-Wave Unitarity",
        "slug": "schwartz-qft-29-4",
    },
    "29.5": {
        "path": "chapters/chapter_29/problems/29_5.tex",
        "title": "Experimental Constraints on the CKM Matrix",
        "slug": "schwartz-qft-29-5",
    },
    "29.6": {
        "path": "chapters/chapter_29/problems/29_6.tex",
        "title": "Phases in the PMNS Matrix",
        "slug": "schwartz-qft-29-6",
    },
    "29.7": {
        "path": "chapters/chapter_29/problems/29_7.tex",
        "title": "Neutrino Oscillations",
        "slug": "schwartz-qft-29-7",
    },
    "29.8": {
        "path": "chapters/chapter_29/problems/29_8.tex",
        "title": "Integrating Out Right-Handed Neutrinos",
        "slug": "schwartz-qft-29-8",
    },
    "29.9": {
        "path": "chapters/chapter_29/problems/29_9.tex",
        "title": "Chiral Rotations and the Theta Angle",
        "slug": "schwartz-qft-29-9",
    },
}

PLACEHOLDER = re.compile(
    r"\\solutionplaceholder|solution\s+to\s+be\s+written|\bTODO\b|\bTBD\b",
    re.IGNORECASE,
)
SOLUTION = re.compile(
    r"\\begin\{solution\}(.*?)\\end\{solution\}", re.DOTALL
)
FIGURE = re.compile(
    r"\\includegraphics(?:\[[^\]]*\])?\s*\{([^}]+)\}"
)


def git_bytes(source: Path, revision: str, relative: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{revision}:{relative}"],
        cwd=source,
        check=True,
        capture_output=True,
    )
    return result.stdout


def git_text(source: Path, revision: str, relative: str) -> str:
    return git_bytes(source, revision, relative).decode("utf-8")


def is_completed(text: str) -> bool:
    match = SOLUTION.search(text)
    if not match:
        return False
    body = match.group(1).strip()
    return len(body) >= 200 and not PLACEHOLDER.search(body)


def web_asset_name(source_path: str) -> str:
    stem = Path(source_path).stem.replace("_", "-")
    return f"schwartz-{stem}.png"


def render_figure(source: Path, revision: str, relative: str) -> str:
    output_name = web_asset_name(relative)
    output_path = ROOT / "assets" / output_name
    with tempfile.TemporaryDirectory(prefix="schwartz-figure-") as temp_dir:
        input_pdf = Path(temp_dir) / "figure.pdf"
        output_prefix = Path(temp_dir) / "figure"
        input_pdf.write_bytes(git_bytes(source, revision, relative))
        subprocess.run(
            [
                "pdftoppm",
                "-png",
                "-singlefile",
                "-r",
                "180",
                str(input_pdf),
                str(output_prefix),
            ],
            check=True,
        )
        output_path.write_bytes(output_prefix.with_suffix(".png").read_bytes())
    return output_name


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

    completed: list[dict[str, str]] = []
    imported_sources: list[str] = []
    rendered_figures: dict[str, str] = {}

    for problem, metadata in PROBLEMS.items():
        text = git_text(source, args.revision, metadata["path"])
        if not is_completed(text):
            continue

        text = re.sub(
            rf"(\\subsection(?:\[[^\]]*\])?)\{{Problem {re.escape(problem)}\}}",
            rf"\1{{Problem {problem}: {metadata['title']}}}",
            text,
            count=1,
        )
        text = text.replace(r"\begin{problemparts}", r"\begin{enumerate}")
        text = text.replace(r"\end{problemparts}", r"\end{enumerate}")
        text = "\n".join(line.rstrip() for line in text.splitlines())

        def replace_figure(match: re.Match[str]) -> str:
            relative = match.group(1)
            if relative not in rendered_figures:
                rendered_figures[relative] = render_figure(
                    source, args.revision, relative
                )
            return f"\\includegraphics{{{rendered_figures[relative]}}}"

        imported_sources.append(FIGURE.sub(replace_figure, text).strip())
        completed.append(
            {
                "problem": problem,
                "title": metadata["title"],
                "slug": metadata["slug"],
                "sourcePath": metadata["path"],
            }
        )

    if not completed:
        raise SystemExit("No completed solutions were found; refusing to publish.")

    document = """% Generated by build/sync_schwartz_qft.py from committed sources only.
% Source repository: https://github.com/Luca-Yucheng-Jin/schwartz-qft-solutions
% Source commit: {commit}
\\documentclass[a4paper,11pt]{{article}}
\\usepackage{{amsmath,amssymb,bm,graphicx,slashed,tikz,tikz-feynman}}
\\DeclareMathOperator{{\\Tr}}{{Tr}}
\\newenvironment{{solution}}{{\\par\\medskip\\noindent\\textbf{{Solution.}}\\par\\smallskip}}{{\\par\\medskip}}
\\newenvironment{{problemparts}}{{\\begin{{enumerate}}\\renewcommand{{\\labelenumi}}{{(\\alph{{enumi}})}}}}{{\\end{{enumerate}}}}
\\title{{Completed Solutions to Schwartz's \\textit{{Quantum Field Theory and the Standard Model}}}}
\\author{{Luca Yucheng Jin}}
\\begin{{document}}
\\maketitle

{body}

\\subsection{{End of imported solutions}}
\\end{{document}}
""".format(commit=commit, body="\n\n".join(imported_sources))
    TEX_OUTPUT.write_text(document, encoding="utf-8")

    manifest = {
        "sourceRepository": "https://github.com/Luca-Yucheng-Jin/schwartz-qft-solutions",
        "sourceCommit": commit,
        "completedProblems": completed,
    }
    MANIFEST_OUTPUT.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        "Imported completed problems: "
        + ", ".join(item["problem"] for item in completed)
    )


if __name__ == "__main__":
    main()
