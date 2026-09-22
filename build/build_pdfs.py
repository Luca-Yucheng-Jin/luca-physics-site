#!/usr/bin/env python3
"""Build every public PDF from its LaTeX source using one house style."""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "tex"
OUTPUT = ROOT / "output" / "pdf"
WORK = ROOT / "tmp" / "pdfs" / "latex"
BUILD = ROOT / "tmp" / "pdfs" / "build"

sys.path.insert(0, str(ROOT / "build"))
from tex_to_html import (  # noqa: E402
    JOBS,
    WHOLE_FILE_PAGES,
    _find_balanced_command_args,
    extract_section_body,
    extract_subsection,
)


@dataclass(frozen=True)
class PdfWork:
    tex_file: str
    slug: str
    title: str
    category: str
    source: str
    body: str
    contents: bool


def tex_text(value: str) -> str:
    """Convert the small amount of HTML in catalogue metadata to LaTeX."""
    value = html.unescape(value)
    value = re.sub(r"<em>(.*?)</em>", r"\\emph{\1}", value)
    value = re.sub(r"<[^>]+>", "", value)
    value = value.replace("&", r"\&")
    return value


def clean_title(value: str) -> str:
    return re.sub(r"\s*\([^)]*\)\s*$", "", value).strip()


def document_body(text: str) -> str:
    """Drop a source preamble/title while keeping its authored document body."""
    first_section = re.search(r"\\section\*?\{", text)
    begin_document = re.search(r"\\begin\{document\}", text)
    if first_section:
        text = text[first_section.start() :]
    elif begin_document:
        text = text[begin_document.end() :]
    end_document = re.search(r"\\end\{document\}", text)
    if end_document:
        text = text[: end_document.start()]
    return text.strip()


def promote_single_outer_section(text: str) -> str:
    """Avoid repeating a wrapper title as a lone outer section heading."""
    sections = _find_balanced_command_args(text, "section")
    subsections = _find_balanced_command_args(text, "subsection")
    if len(sections) != 1 or not subsections:
        return text
    _, end, _ = sections[0]
    text = text[end:].lstrip()
    text = re.sub(r"\\subsubsection(\*?)", r"\\LUCAOLDsubsubsection\1", text)
    text = re.sub(r"\\subsection(\*?)", r"\\section\1", text)
    text = re.sub(r"\\LUCAOLDsubsubsection(\*?)", r"\\subsection\1", text)
    return text


def prepare_body(text: str) -> str:
    """Remove source-only constructs unavailable in the public checkout."""
    text = text.replace("，", ",")
    # A bare row separator in a cases block is invalid LaTeX (and visually
    # contributes only vertical whitespace in the HTML edition).
    text = re.sub(r"(?m)^[ \t]*\\\\[ \t]*$", "", text)
    for environment in ("equation", "equation*", "align", "align*", "gather", "gather*", "multline", "multline*"):
        pattern = re.compile(
            rf"(\\begin\{{{re.escape(environment)}\}})(.*?)(\\end\{{{re.escape(environment)}\}})",
            re.DOTALL,
        )
        text = pattern.sub(
            lambda match: match.group(1)
            + re.sub(r"\n[ \t]*\n", "\n", match.group(2))
            + match.group(3),
            text,
        )

    def break_implicit_aligned_rows(match: re.Match[str]) -> str:
        lines = match.group(2).splitlines()
        seen_content = False
        for index, line in enumerate(lines):
            if not line.strip():
                continue
            if seen_content and re.match(r"^[ \t]*&", line):
                previous = index - 1
                while previous >= 0 and not lines[previous].strip():
                    previous -= 1
                if previous >= 0 and not re.search(
                    r"\\\\(?:\[[^\]]*\])?[ \t]*$", lines[previous]
                ):
                    lines[previous] = lines[previous].rstrip() + r" \\"
            seen_content = True
        return match.group(1) + "\n".join(lines) + match.group(3)

    text = re.sub(
        r"(\\begin\{(?:aligned|align\*?)\})(.*?)(\\end\{(?:aligned|align\*?)\})",
        break_implicit_aligned_rows,
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\\includegraphics\s*\{",
        r"\\includegraphics[width=\\linewidth]{",
        text,
    )
    # The supplied breakable solution boxes and long boxed derivations leave
    # little room for deferred floats.  Place source figures where introduced.
    text = re.sub(
        r"\\begin\{figure\}(?:\[[^]]*\])?",
        r"\\begin{figure}[H]",
        text,
    )
    # This source-side figure was never imported into the public repository;
    # the HTML edition also omits it.  Keep the surrounding authored text.
    text = re.sub(
        r"\\begin\{figure\}.*?\\input\{fig/flow\.tex\}.*?\\end\{figure\}",
        "",
        text,
        flags=re.DOTALL,
    )
    return text


def category_from_breadcrumb(breadcrumb: str) -> str:
    return tex_text(breadcrumb.split("·", 1)[0].strip())


def collect_works() -> list[PdfWork]:
    works: list[PdfWork] = []
    for tex_file, jobs in JOBS:
        text = (TEX / tex_file).read_text(encoding="utf-8")
        for needle, slug, breadcrumb, source in jobs:
            title, body = extract_subsection(text, needle)
            if body is None:
                raise RuntimeError(f"Could not find {needle!r} in {tex_file}")
            works.append(
                PdfWork(
                    tex_file,
                    slug,
                    clean_title(title),
                    category_from_breadcrumb(breadcrumb),
                    source,
                    prepare_body(body.strip()),
                    False,
                )
            )

    qftsoln = (TEX / "QFTsoln.tex").read_text(encoding="utf-8")
    title, body = extract_section_body(qftsoln, "Final Project")
    if body is None:
        raise RuntimeError("Could not find the Peskin final project")
    works.append(
        PdfWork(
            "QFTsoln.tex",
            "peskin-final",
            title.strip(),
            "Quantum Field Theory",
            "Peskin &amp; Schroeder, <em>An Introduction to Quantum Field Theory</em>, end-of-book final project.",
            prepare_body(body.strip()),
            len(_find_balanced_command_args(body, "subsection")) >= 3,
        )
    )

    for tex_file, slug, title, breadcrumb, source in WHOLE_FILE_PAGES:
        text = (TEX / tex_file).read_text(encoding="utf-8")
        body = prepare_body(promote_single_outer_section(document_body(text)))
        heading_count = len(_find_balanced_command_args(body, "section"))
        works.append(
            PdfWork(
                tex_file,
                slug,
                title,
                category_from_breadcrumb(breadcrumb),
                source,
                body,
                heading_count >= 3,
            )
        )

    by_slug = {work.slug: work for work in works}
    if len(by_slug) != len(works):
        raise RuntimeError("Duplicate PDF slugs found")
    return works


def wrapper(work: PdfWork) -> str:
    toc = "\\tableofcontents\n" if work.contents else ""
    equation_numbering = (
        "\\renewcommand{\\theequation}{\\arabic{equation}}\n"
        if not re.search(r"\\section\*?\{", work.body)
        else ""
    )
    return rf"""% Generated from tex/{work.tex_file}; do not edit this wrapper.
\documentclass[11pt,a4paper]{{article}}
\pdfvariable objcompresslevel=0
\usepackage[manualbib]{{elegantphys}}
\usepackage{{luca-pdf-compat}}
\hypersetup{{pdftitle={{{tex_text(work.title)}}},pdfauthor={{Yucheng (Luca) Jin}}}}
\begin{{document}}
\makecover{{{tex_text(work.title)}}}{{{tex_text(work.source)}}}{{Yucheng (Luca) Jin}}{{{work.category}}}
\markboth{{{work.category}}}{{{work.category}}}
{equation_numbering}{toc}{work.body}
\end{{document}}
"""


def run_latex(work: PdfWork) -> None:
    source = WORK / f"{work.slug}.tex"
    source.write_text(wrapper(work), encoding="utf-8")
    # A font-stack change can leave engine-specific commands in an old TOC or
    # AUX file.  Each public edition is cheap enough to build from clean
    # intermediates, which also makes local and CI output deterministic.
    for suffix in (".aux", ".toc", ".out", ".fdb_latexmk", ".fls", ".log", ".pdf"):
        stale = BUILD / f"{work.slug}{suffix}"
        if stale.exists():
            stale.unlink()
    env = os.environ.copy()
    texinputs = os.pathsep.join((str(TEX), str(ROOT / "assets"), ""))
    env["TEXINPUTS"] = texinputs
    tex_cache = BUILD / "texmf-cache"
    tex_cache.mkdir(parents=True, exist_ok=True)
    env["TEXMFVAR"] = str(tex_cache)
    env["TEXMFCACHE"] = str(tex_cache)
    env["XDG_CACHE_HOME"] = str(BUILD / "xdg-cache")
    env["PATH"] = os.pathsep.join(("/opt/homebrew/bin", env.get("PATH", "")))
    command = [
        "/opt/homebrew/bin/latexmk",
        "-g",
        "-lualatex",
        "-interaction=nonstopmode",
        "-halt-on-error",
        f"-outdir={BUILD}",
        str(source),
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        log = BUILD / f"{work.slug}.log"
        detail = log.read_text(encoding="utf-8", errors="replace") if log.exists() else result.stdout
        tail = "\n".join(detail.splitlines()[-80:])
        raise RuntimeError(f"LaTeX failed for {work.slug}:\n{tail}")
    pdf = BUILD / f"{work.slug}.pdf"
    if not pdf.exists():
        raise RuntimeError(f"LaTeX produced no PDF for {work.slug}")
    shutil.copy2(pdf, OUTPUT / pdf.name)
    print(f"  wrote output/pdf/{pdf.name}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("slugs", nargs="*", help="Optional public note slugs")
    args = parser.parse_args()
    requested = set(args.slugs)

    works = collect_works()
    if requested:
        known = {work.slug for work in works}
        missing = requested - known
        if missing:
            raise SystemExit("Unknown PDF slug(s): " + ", ".join(sorted(missing)))
        works = [work for work in works if work.slug in requested]

    WORK.mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    failures: list[tuple[str, str]] = []
    for work in works:
        try:
            run_latex(work)
        except RuntimeError as error:
            failures.append((work.slug, str(error)))
            print(f"  failed output/pdf/{work.slug}.pdf", file=sys.stderr)
    if failures:
        details = "\n\n".join(message for _, message in failures)
        raise RuntimeError(
            f"Failed to build {len(failures)} of {len(works)} PDFs:\n{details}"
        )
    print(f"Generated {len(works)} elegantphys PDF edition(s).")


if __name__ == "__main__":
    main()
