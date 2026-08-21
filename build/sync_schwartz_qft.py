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
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_OUTPUT = ROOT / "assets" / "schwartz-qft-manifest.json"

PROBLEM_PATH = re.compile(
    r"^chapters/chapter_(\d+)/problems/(\d+)_(\d+)\.tex$"
)
SUBSECTION = re.compile(
    r"\\subsection(?:\[([^\]]+)\])?\{([^{}]+)\}"
)

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


def git_paths(source: Path, revision: str) -> list[str]:
    result = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", revision, "chapters"],
        cwd=source,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.splitlines()


def is_completed(text: str) -> bool:
    match = SOLUTION.search(text)
    if not match:
        return False
    body = match.group(1).strip()
    return len(body) >= 200 and not PLACEHOLDER.search(body)


def problem_title(text: str, problem: str) -> str:
    match = SUBSECTION.search(text)
    if not match:
        return f"Problem {problem}"
    label = (match.group(1) or match.group(2)).strip()
    title = re.sub(
        rf"^Problem\s+{re.escape(problem)}\s*:?\s*",
        "",
        label,
        flags=re.IGNORECASE,
    ).strip()
    return title or f"Problem {problem}"


def chapter_titles(source: Path, revision: str, chapter: str) -> tuple[str, str]:
    chapter_path = f"chapters/chapter_{chapter}/chapter_{chapter}.tex"
    text = git_text(source, revision, chapter_path)
    match = re.search(
        rf"\\section\{{Chapter\s+{re.escape(chapter)}:\s*(.*?)\}}",
        text,
    )
    latex_title = match.group(1).strip() if match else "Completed solutions"
    display_title = latex_title.replace("--", "–")
    return latex_title, display_title


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

    completed_by_chapter: dict[str, list[dict[str, str]]] = defaultdict(list)
    sources_by_chapter: dict[str, list[str]] = defaultdict(list)
    rendered_figures: dict[str, str] = {}

    problem_paths = []
    for relative in git_paths(source, args.revision):
        match = PROBLEM_PATH.match(relative)
        if match:
            chapter, file_chapter, problem_number = match.groups()
            if chapter == file_chapter:
                problem_paths.append((int(chapter), int(problem_number), relative))

    for chapter_number, problem_number, relative in sorted(problem_paths):
        chapter = str(chapter_number)
        problem = f"{chapter}.{problem_number}"
        text = git_text(source, args.revision, relative)
        if not is_completed(text):
            continue

        title = problem_title(text, problem)

        text = re.sub(
            rf"(\\subsection(?:\[[^\]]*\])?)\{{Problem {re.escape(problem)}\}}",
            lambda match: f"{match.group(1)}{{Problem {problem}: {title}}}",
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

        sources_by_chapter[chapter].append(FIGURE.sub(replace_figure, text).strip())
        completed_by_chapter[chapter].append(
            {
                "problem": problem,
                "title": title,
                "sourcePath": relative,
            }
        )

    if not completed_by_chapter:
        raise SystemExit("No completed solutions were found; refusing to publish.")

    chapters = []
    for chapter in sorted(completed_by_chapter, key=int):
        latex_title, display_title = chapter_titles(source, args.revision, chapter)
        slug = f"schwartz-qft-chapter-{chapter}"
        tex_filename = f"{slug}.tex"
        document = """% Generated by build/sync_schwartz_qft.py from committed sources only.
% Source repository: https://github.com/Luca-Yucheng-Jin/schwartz-qft-solutions
% Source commit: {commit}
\\documentclass[a4paper,11pt]{{article}}
\\usepackage{{amsmath,amssymb,bm,graphicx,slashed,tikz,tikz-feynman}}
\\DeclareMathOperator{{\\Tr}}{{Tr}}
\\newenvironment{{solution}}{{\\par\\medskip\\noindent\\textbf{{Solution.}}\\par\\smallskip}}{{\\par\\medskip}}
\\newenvironment{{problemparts}}{{\\begin{{enumerate}}\\renewcommand{{\\labelenumi}}{{(\\alph{{enumi}})}}}}{{\\end{{enumerate}}}}
\\title{{Schwartz Chapter {chapter}: {chapter_title}}}
\\author{{Luca Yucheng Jin}}
\\begin{{document}}
\\maketitle

\\section{{Completed Problems}}

{body}

\\end{{document}}
""".format(
            commit=commit,
            chapter=chapter,
            chapter_title=latex_title,
            body="\n\n".join(sources_by_chapter[chapter]),
        )
        (ROOT / "tex" / tex_filename).write_text(document, encoding="utf-8")
        chapters.append(
            {
                "chapter": chapter,
                "title": display_title,
                "slug": slug,
                "texFile": tex_filename,
                "completedProblems": completed_by_chapter[chapter],
            }
        )

    manifest = {
        "sourceRepository": "https://github.com/Luca-Yucheng-Jin/schwartz-qft-solutions",
        "sourceCommit": commit,
        "chapters": chapters,
    }
    MANIFEST_OUTPUT.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        "Imported completed problems: "
        + ", ".join(
            problem["problem"]
            for chapter in chapters
            for problem in chapter["completedProblems"]
        )
    )


if __name__ == "__main__":
    main()
