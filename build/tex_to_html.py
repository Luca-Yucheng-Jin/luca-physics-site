#!/usr/bin/env python3
"""
Convert each \\subsection{...} block from the project's .tex files into a fully
rendered HTML notes page. Math is preserved so MathJax can typeset it; LaTeX
structure (sections, lists, formatting) is converted to HTML.

Mapping of files → output slugs is hard-coded so it matches the catalogue links
in notes.html.
"""

import re
import os
import html as htmllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEX  = os.path.join(ROOT, "tex")
OUT  = os.path.join(ROOT, "notes")

# subsection-title (regex-matched, lowercased substring is enough) → slug, source
# we anchor on a unique substring of each subsection title in the .tex
JOBS = [
    # ---- QM.tex ----
    ("QM.tex", [
        ("non-degeneracy and reality of bound states", "qm-bound-states",
            "Quantum Mechanics · Tong PS1 Q3",
            "D. Tong, <em>Quantum Mechanics</em>, Problem Sheet 1, Question 3."),
        ("absence of odd-parity bound states",          "qm-shallow-well",
            "Quantum Mechanics · Tong PS1 Q7",
            "D. Tong, <em>Quantum Mechanics</em>, Problem Sheet 1, Question 7."),
        ("factorisation method for the sech",           "qm-sech-squared",
            "Quantum Mechanics · Tong PS1 Q8",
            "D. Tong, <em>Quantum Mechanics</em>, Problem Sheet 1, Question 8."),
    ]),
    # ---- ED.tex ----
    ("ED.tex", [
        ("retarded potentials and far-field",     "ed-retarded",
            "Electrodynamics · Tong EM PS7 Q4",
            "D. Tong, <em>Electromagnetism</em>, Problem Sheet 7, Question 4."),
        ("liénard--wiechert potential",          "ed-lienard-wiechert",
            "Electrodynamics · Tong EM PS7 Q6",
            "D. Tong, <em>Electromagnetism</em>, Problem Sheet 7, Question 6."),
        ("relativistic motion in a uniform",      "ed-relativistic-uniform",
            "Electrodynamics · Tong EM PS3 Q9",
            "D. Tong, <em>Electromagnetism</em>, Problem Sheet 3, Question 9."),
        ("gauge transformation of a plane",       "ed-gauge-plane-wave",
            "Electrodynamics · Tong EM PS3 Q5",
            "D. Tong, <em>Electromagnetism</em>, Problem Sheet 3, Question 5."),
        ("reflection of an electromagnetic wave from a moving", "ed-moving-mirror",
            "Electrodynamics · Tong EM PS3 Q7",
            "D. Tong, <em>Electromagnetism</em>, Problem Sheet 3, Question 7."),
        ("covariant form of ohm",                "ed-covariant-ohms",
            "Electrodynamics · Tong EM PS3 Q10",
            "D. Tong, <em>Electromagnetism</em>, Problem Sheet 3, Question 10."),
        ("dielectric sphere in a uniform",       "ed-dielectric-sphere",
            "Electrodynamics · Tong EM PS8 Q1",
            "D. Tong, <em>Electromagnetism</em>, Problem Sheet 8, Question 1."),
        ("frustrated total internal reflection", "ed-frustrated-tir",
            "Electrodynamics · Tong EM PS8 Q3",
            "D. Tong, <em>Electromagnetism</em>, Problem Sheet 8, Question 3."),
    ]),
    # ---- MM.tex ----
    ("MM.tex", [
        ("jordan's lemma",                       "mm-jordans-lemma",
            "Mathematical Methods · Complex Analysis",
            "Standard complex-analysis result; treatment follows J. E. Santos' Cambridge IB lectures."),
        ("convolution of $e",                    "mm-convolution-fourier",
            "Mathematical Methods · Santos PS3 Q2",
            "J. E. Santos, Cambridge Part IB Complex Methods, Problem Sheet 3, Question 2."),
        ("residues at simple poles",             "mm-residues",
            "Mathematical Methods · Santos PS2 Q7",
            "J. E. Santos, Cambridge Part IB Complex Methods, Problem Sheet 2, Question 7."),
        ("contour integration via residue",      "mm-contour-integration",
            "Mathematical Methods · Santos PS2 Q9",
            "J. E. Santos, Cambridge Part IB Complex Methods, Problem Sheet 2, Question 9."),
        ("laplace transform of",                 "mm-laplace-bromwich",
            "Mathematical Methods · Santos PS3 Q12",
            "J. E. Santos, Cambridge Part IB Complex Methods, Problem Sheet 3, Question 12."),
        ("variational derivation of euler",      "mm-variational-euler",
            "Mathematical Methods · Cambridge Part II Var. Principles PS2 Q9",
            "Cambridge Part II Variational Principles, Problem Sheet 2, Question 9."),
    ]),
    # ---- DE.tex ----
    ("DE.tex", [
        ("green's function for a second-order",  "de-greens-function",
            "Differential Equations · Imperial Contaldi PS9 Q4",
            "Imperial College London, Carlo Contaldi, Differential Equations, Problem Sheet 9, Question 4."),
        ("laplace operator in 3d",               "de-images-laplace",
            "Differential Equations · Imperial Contaldi PS9 Q5",
            "Imperial College London, Carlo Contaldi, Differential Equations, Problem Sheet 9, Question 5."),
        ("green's identity and method of images","de-greens-identity-halfspace",
            "Differential Equations · Cambridge IB 2025, 14D",
            "Cambridge Tripos Part IB past paper 2025, Question 14D."),
    ]),
    # ---- TDSP.tex ----
    ("TDSP.tex", [
        ("joule-thomson process",                "tdsp-joule-thomson",
            "Thermo &amp; Stat Phys · Tong SP PS4 Q4",
            "D. Tong, <em>Statistical Physics</em>, Problem Sheet 4, Question 4."),
        ("adiabatic compression of water",       "tdsp-adiabatic-water",
            "Thermo &amp; Stat Phys · Imperial 2023 TPSM Q3",
            "Imperial College London, 2023 Thermodynamics &amp; Properties of Matter exam, Question 3."),
        ("partition function and thermodynamics","tdsp-spin-half",
            "Thermo &amp; Stat Phys · Tong SP PS1 Q3",
            "D. Tong, <em>Statistical Physics</em>, Problem Sheet 1, Question 3."),
        ("heat capacity of an interacting",      "tdsp-interacting-spin",
            "Thermo &amp; Stat Phys · Tong SP PS1 Q4",
            "D. Tong, <em>Statistical Physics</em>, Problem Sheet 1, Question 4."),
    ]),
    # ---- QFTsoln.tex (Peskin solutions) ----
    # peskin-6-2 already exists with curated content; we still regenerate it.
    ("QFTsoln.tex", [
        ("equivalent photon approximation",      "peskin-6-2",
            "Quantum Field Theory · Peskin Problem 6.2",
            "Peskin &amp; Schroeder, <em>An Introduction to Quantum Field Theory</em>, Problem 6.2."),
        ("alternative regulators in qed",        "peskin-7",
            "Quantum Field Theory · Peskin Chapter 7",
            "Peskin &amp; Schroeder, <em>An Introduction to Quantum Field Theory</em>, Chapter 7."),
    ]),
]

# QFTschwartz.tex is structured as \section + \subsection. We convert each
# subsection into its own page later; for now we skip it and convert per-file.
# (Handled separately below.)

# ----------------------------------------------------------------------
# LaTeX → HTML conversion
# ----------------------------------------------------------------------

def _find_balanced_command_args(text, command):
    """Find every `\\command{ARG}` with balanced braces. Returns a list of
    tuples (start_of_command, end_after_closing_brace, arg_text)."""
    out = []
    pat = re.compile(r"\\" + re.escape(command) + r"\*?")
    for m in pat.finditer(text):
        j = m.end()
        # skip optional [opts]
        while j < len(text) and text[j] == " ":
            j += 1
        if j < len(text) and text[j] == "[":
            depth = 1; j += 1
            while j < len(text) and depth > 0:
                if text[j] == "[": depth += 1
                elif text[j] == "]": depth -= 1
                j += 1
        while j < len(text) and text[j] == " ":
            j += 1
        if j >= len(text) or text[j] != "{":
            continue
        depth = 1; j += 1; start = j
        while j < len(text) and depth > 0:
            if text[j] == "{": depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0: break
            j += 1
        arg = text[start:j]
        out.append((m.start(), j + 1, arg))
    return out


def extract_subsection(text, needle):
    """Find the \\subsection{...} whose title contains `needle` (lowercase
    substring) and return the body, stopping at the next \\subsection or
    \\section."""
    needle = needle.lower()
    matches = _find_balanced_command_args(text, "subsection")
    for i, (cstart, cend, title) in enumerate(matches):
        if needle in title.lower():
            start = cend
            end = matches[i + 1][0] if i + 1 < len(matches) else len(text)
            next_section = re.search(r"\\section\*?\{", text[start:end])
            if next_section:
                end = start + next_section.start()
            return title, text[start:end]
    return None, None


# Math placeholders: we extract math regions and replace them with sentinels
# while we transform the surrounding text, then restore them.


def _rewrite_tr_curly(body):
    """Rewrite \\Tr{X} → \\operatorname{Tr}\\!\\left(X\\right) (auto-sized
    parens). Only the curly form is rewritten — the bracket form
    \\Tr[X] is intentional notation for literal Tr[X] in the source
    and is left alone (the runtime macro `\\Tr` → `\\operatorname{Tr}`
    handles those, rendering them as Tr[X]).

    Done with balanced-brace matching so nested {} inside the argument
    survive (e.g. \\Tr{\\gamma^\\mu \\gamma^\\nu \\frac{1}{p^2}} →
    Tr(...) including the \\frac arg)."""
    out = []
    i = 0
    pat = re.compile(r"\\Tr(?![A-Za-z])\s*\{")
    while i < len(body):
        m = pat.search(body, i)
        if not m:
            out.append(body[i:])
            break
        out.append(body[i:m.start()])
        depth = 1
        j = m.end()
        start = j
        while j < len(body) and depth > 0:
            if body[j] == "{":
                depth += 1
            elif body[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        arg = body[start:j]
        out.append(f"\\operatorname{{Tr}}\\!\\left({arg}\\right)")
        i = j + 1
    return "".join(out)


def _rewrite_tensor(body):
    """Rewrite \\tensor{base}{indices} → base + <indices with empty groups>
    so MathJax doesn't stack the upper and lower indices in the same
    horizontal column.

    Real LaTeX's `tensor.sty` distributes the indices: μ goes above-left
    and the lower indices go below-right of where μ ended. MathJax does
    this naturally if and only if there's an empty {} between consecutive
    script operators — `R^\\mu{}_{\\nu\\rho\\sigma}`. The polyfill
    `tensor: ['{#1{#2}}', 2]` produced `R^\\mu_{\\nu\\rho\\sigma}` which
    stacks them in one column instead.

    We walk the indices argument and insert {} before each ^/_ operator
    that follows another, so the kerning shifts correctly.

    Examples (all verified against pdfLaTeX):
      \\tensor{R}{^\\mu_{\\nu\\rho\\sigma}}    →  R^\\mu{}_{\\nu\\rho\\sigma}
      \\tensor{G}{_\\nu^{\\beta\\rho\\sigma}}  →  G_\\nu{}^{\\beta\\rho\\sigma}
      \\tensor{T}{^{\\mu\\nu}_{\\rho\\sigma}}  →  T^{\\mu\\nu}{}_{\\rho\\sigma}
      \\tensor{R}{_{\\mu\\nu\\rho\\sigma}}     →  R_{\\mu\\nu\\rho\\sigma}    (no transition; pass-through)

    Composes with accents: \\bar{\\tensor{R}{^\\mu_\\nu}} expands to
    \\bar{R^\\mu{}_\\nu} which renders correctly under MathJax.

    Source today uses only \\tensor; \\indices and \\prescript aren't
    triggered yet. Easy to extend when needed."""
    out = []
    i = 0
    pat = re.compile(r"\\tensor\s*\{")
    while i < len(body):
        m = pat.search(body, i)
        if not m:
            out.append(body[i:])
            break
        out.append(body[i:m.start()])
        # Parse arg1 (base): balanced { ... }
        depth = 1
        j = m.end()
        start = j
        while j < len(body) and depth > 0:
            if body[j] == "{": depth += 1
            elif body[j] == "}":
                depth -= 1
                if depth == 0: break
            j += 1
        if depth != 0:                           # malformed; bail
            out.append(body[m.start():])
            break
        base = body[start:j]
        j += 1                                    # past closing brace
        # Skip whitespace, expect arg2's {
        while j < len(body) and body[j] in " \n\t":
            j += 1
        if j >= len(body) or body[j] != "{":
            # No second arg — emit base alone
            out.append(base)
            i = j
            continue
        depth = 1
        j += 1
        start = j
        while j < len(body) and depth > 0:
            if body[j] == "{": depth += 1
            elif body[j] == "}":
                depth -= 1
                if depth == 0: break
            j += 1
        indices = body[start:j]
        i = j + 1                                 # past closing brace of arg2
        # Walk indices, inserting {} between consecutive script operators
        rewritten = base + _split_tensor_indices(indices)
        # Leading-edge fix: if the base starts with a letter and we're
        # emerging at the end of a control word (e.g. `\delta\tensor{R}{…}`),
        # the substitution would glue `R` onto `\delta` and form the bogus
        # macro `\deltaR`. Insert `{}` to terminate the preceding word.
        if rewritten and rewritten[0].isalpha():
            prev = "".join(out)
            if prev:
                k = len(prev) - 1
                while k >= 0 and prev[k].isalpha():
                    k -= 1
                if k >= 0 and prev[k] == "\\":
                    rewritten = "{}" + rewritten
        # Trailing-edge fix: if the rewrite ends with a control word
        # (e.g. last index was `^\nu`, so output ends `…\nu`) AND the
        # next source character after the original \tensor{}{…} is a
        # letter, the two glue together (`\nu` + `x` → `\nux`).
        # Append `{}` to terminate the trailing control word.
        if i < len(body) and body[i].isalpha():
            k = len(rewritten) - 1
            while k >= 0 and rewritten[k].isalpha():
                k -= 1
            if k >= 0 and rewritten[k] == "\\":
                rewritten = rewritten + "{}"
        out.append(rewritten)
    return "".join(out)


def _split_tensor_indices(s):
    """Walk a tensor-index string and insert empty groups {} between each
    pair of consecutive ^/_ operators so MathJax doesn't collapse them
    into one stacked column. Returns the rewritten string."""
    out = []
    i = 0
    seen_script = False
    n = len(s)
    while i < n:
        ch = s[i]
        if ch in "^_":
            if seen_script:
                out.append("{}")
            out.append(ch)
            i += 1
            # consume the script's argument: balanced {...}, or \cmd, or single char
            while i < n and s[i] in " \t":
                i += 1
            if i >= n: break
            if s[i] == "{":
                depth = 1
                start = i
                i += 1
                while i < n and depth > 0:
                    if s[i] == "{": depth += 1
                    elif s[i] == "}": depth -= 1
                    i += 1
                out.append(s[start:i])
            elif s[i] == "\\":
                start = i
                i += 1
                while i < n and (s[i].isalpha() or s[i] == "*"):
                    i += 1
                out.append(s[start:i])
            else:
                out.append(s[i])
                i += 1
            seen_script = True
        else:
            # Non-script char: pass through. (Whitespace etc. between the
            # operators is fine — it doesn't reset `seen_script`.)
            out.append(ch)
            i += 1
    return "".join(out)


class MathStash(dict):
    """Holds math + tikz stashes, plus a per-page equation counter, a
    figure counter, and a label→number map so \\eqref / \\ref resolve.

    Equation numbers are formatted (n.eq) where n is the index of the
    current `<h2>` topic on the page (1-indexed) and eq resets at every
    new topic. This mirrors `\\numberwithin{equation}{section}` in the
    user's elegantphys.sty preamble."""
    def __init__(self):
        super().__init__()
        self.items = []
        self["tikz"] = []
        self["sec_counter"] = 1   # default for single-section pages
        self["eq_counter"] = 0
        self["fig_counter"] = 0
        self["labels"] = {}       # \label{...} → number string
        self._section_started = False

    def next_eq_number(self):
        self["eq_counter"] += 1
        return f"{self['sec_counter']}.{self['eq_counter']}"

    def begin_section(self):
        """Mark the start of a new <h2> topic. Resets the equation counter,
        and on every call AFTER the first, increments the section counter
        so the new equation tags read (n+1.1), (n+1.2), …"""
        if self._section_started:
            self["sec_counter"] += 1
        self["eq_counter"] = 0
        self._section_started = True

    # Backwards-compat shim for callers that still use the old name.
    reset_eq_counter = begin_section

    def stash(self, body, display):
        body = _rewrite_tr_curly(body)
        body = _rewrite_tensor(body)
        idx = len(self.items)
        self.items.append((body, display))
        return f"\x00MATH{idx}\x00"

    def restore(self, text):
        def html_safe_math(b):
            # Math text often contains `<`, `>`, `&` (e.g. `x < 1`). The HTML
            # parser interprets these before MathJax sees them, so we must
            # encode them — MathJax accepts &lt; / &gt; / &amp; inside $..$.
            return (b.replace("&", "&amp;")
                     .replace("<", "&lt;")
                     .replace(">", "&gt;"))
        def repl(m):
            idx = int(m.group(1))
            body, display = self.items[idx]
            body = html_safe_math(body)
            if display:
                return f"\\[{body}\\]"
            return f"${body}$"
        return re.sub(r"\x00MATH(\d+)\x00", repl, text)


DISPLAY_ENVS = ["equation", "equation*", "align", "align*", "gather", "gather*",
                "multline", "multline*"]


def _strip_two_arg_keep_second(text, command):
    """For commands of the form \\command[opt]{arg1}{arg2} (where arg1 is
    decoration metadata we don't care about and arg2 is the actual content
    we want to keep), rewrite each occurrence to just the contents of arg2.
    Optional `[opt]` arguments are also tolerated. The braces are matched
    with balance so nested {} survive."""
    out = []
    i = 0
    pat = re.compile(r"\\" + re.escape(command) + r"\*?")
    while i < len(text):
        m = pat.search(text, i)
        if not m:
            out.append(text[i:])
            break
        out.append(text[i:m.start()])
        j = m.end()
        # optional [opt]
        while j < len(text) and text[j] == " ": j += 1
        if j < len(text) and text[j] == "[":
            depth = 1; j += 1
            while j < len(text) and depth > 0:
                if text[j] == "[": depth += 1
                elif text[j] == "]": depth -= 1
                j += 1
        # arg1 - eat
        while j < len(text) and text[j] == " ": j += 1
        if j >= len(text) or text[j] != "{":
            out.append(text[m.start():m.end()])
            i = m.end()
            continue
        depth = 1; j += 1
        while j < len(text) and depth > 0:
            if text[j] == "{": depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0: break
            j += 1
        j += 1   # past closing brace of arg1
        # arg2 - keep contents
        while j < len(text) and text[j] in " \n\t": j += 1
        if j >= len(text) or text[j] != "{":
            i = j
            continue
        depth = 1; j += 1; arg2_start = j
        while j < len(text) and depth > 0:
            if text[j] == "{": depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0: break
            j += 1
        out.append(text[arg2_start:j])
        i = j + 1
    return "".join(out)


def _balanced_arg_replace(text, command, replacer):
    """Find every `\\command{...}` in `text` (where the braces are balanced,
    so nested {} are handled) and replace each match with `replacer(arg)`.
    `command` is the literal command name without the backslash, e.g.
    'subsection' or 'textbf'. Trailing star is allowed."""
    out = []
    i = 0
    pat = re.compile(r"\\" + re.escape(command) + r"\*?")
    while i < len(text):
        m = pat.search(text, i)
        if not m:
            out.append(text[i:])
            break
        out.append(text[i:m.start()])
        j = m.end()
        # Skip optional [opts] argument (some commands accept one)
        while j < len(text) and text[j] == " ":
            j += 1
        if j < len(text) and text[j] == "[":
            depth = 1
            j += 1
            while j < len(text) and depth > 0:
                if text[j] == "[":
                    depth += 1
                elif text[j] == "]":
                    depth -= 1
                j += 1
        # Skip whitespace before {
        while j < len(text) and text[j] == " ":
            j += 1
        if j >= len(text) or text[j] != "{":
            # No argument — leave the literal as-is
            out.append(text[m.start():m.end()])
            i = m.end()
            continue
        depth = 1
        j += 1
        start = j
        while j < len(text) and depth > 0:
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        arg = text[start:j]
        out.append(replacer(arg))
        i = j + 1
    return "".join(out)


def strip_tex_only_constructs(text):
    """Remove LaTeX-only constructs that have no HTML equivalent. TikZ is
    handled separately (preserved); only purely typographical commands are
    stripped here."""

    # spacing & layout commands with no semantic content
    text = re.sub(r"\\v(?:space|fill)\*?\{[^}]*\}", "", text)
    text = re.sub(r"\\h(?:space|fill)\*?\{[^}]*\}", " ", text)
    text = re.sub(r"\\(?:newpage|clearpage|pagebreak|linebreak|nopagebreak|flushbottom|raggedbottom|onehalfspacing|doublespacing|singlespacing)\b", "", text)
    text = re.sub(r"\\setlength\{[^}]+\}\{[^}]+\}", "", text)
    text = re.sub(r"\\addtolength\{[^}]+\}\{[^}]+\}", "", text)
    text = re.sub(r"\\baselineskip\b", "", text)
    # \raisebox{lift}{content} → keep only content
    for cmd in ("raisebox", "makebox", "framebox", "fbox", "parbox", "mbox"):
        text = _strip_two_arg_keep_second(text, cmd)
    # Single-arg layout commands like \vcenter{...}, \hbox{...}, \text{...}
    # used inline with math to wrap a tikzpicture. Keep the inner content.
    for cmd in ("vcenter", "hbox", "vbox"):
        text = _balanced_arg_replace(text, cmd, lambda a: a)

    # \begin{shaded}…\end{shaded} typically wraps a boxed key result like
    # the Euler-Lagrange equation or the Noether current. Render as a
    # styled <aside class="boxed-equation"> matching elegantphys.sty's
    # \boxedeq{X} style (lightgray bg, thin black frame). Previously
    # silently stripped — losing the visual emphasis the user intended.
    text = re.sub(r"\\begin\{shaded\}",
                  '\n\n<aside class="boxed-equation">\n\n', text)
    text = re.sub(r"\\end\{shaded\}",
                  '\n\n</aside>\n\n', text)

    # tcolorbox — colored callout boxes. Render as <aside>.
    text = re.sub(r"\\begin\{tcolorbox\}(?:\[[^\]]*\])?",
                  '\n\n<aside class="callout">\n\n', text)
    text = re.sub(r"\\end\{tcolorbox\}",
                  '\n\n</aside>\n\n', text)

    # Solution markers come in three shapes across the .tex sources:
    #   \begin{solution}...\end{solution}        (Tong PS files)
    #   \underline{\textbf{Solution}} ...         (QM, DE, MM, TDSP, ED)
    #   \textbf{Solution:} ...                    (same files, sometimes)
    # Normalise the latter two into the env form so a single styled
    # <aside class="solution"> covers all pages — matches the user's
    # elegantphys.sty \begin{solution}{...}\end{solution} tcolorbox.
    if r"\begin{solution}" not in text:
        sol_pat = re.compile(
            r"(?:\\noindent\s*)?"
            r"(?:\\underline\s*\{\s*\\textbf\s*\{Solution[.:]?\}\s*\}"
            r"|\\textbf\s*\{Solution[.:]?\})"
        )
        m = sol_pat.search(text)
        if m:
            text = (text[:m.start()]
                    + r"\begin{solution}"
                    + text[m.end():]
                    + r"\end{solution}")

    # \begin{solution}…\end{solution} → styled <aside>. The "Solution."
    # label is rendered by CSS (::before) so it floats inline with the
    # first paragraph rather than sitting on a line of its own.
    text = re.sub(r"\\begin\{solution\}",
                  '\n\n<aside class="solution">\n\n',
                  text)
    text = re.sub(r"\\end\{solution\}",
                  '\n\n</aside>\n\n', text)

    # titlepage — strip entirely (we already use our own header)
    text = re.sub(r"\\begin\{titlepage\}.*?\\end\{titlepage\}",
                  "", text, flags=re.DOTALL)

    # axis / pgfplots — not supported by TikZJax; show as source listing
    def _axis_repl(m):
        body = m.group(0)
        safe = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return ('\n\n<figure class="tikz-source"><pre>'
                + safe +
                '</pre><figcaption>pgfplots figure — auto-render not available.</figcaption></figure>\n\n')
    text = re.sub(r"\\begin\{axis\}.*?\\end\{axis\}",
                  _axis_repl, text, flags=re.DOTALL)

    # tabular — minimal HTML table conversion (rows on \\, cells on &).
    def _tabular_repl(m):
        spec = m.group(1) or ""    # the column-spec we ignore
        body = m.group(2).strip()
        rows = re.split(r"\\\\\s*", body)
        out = ['<table class="note__table">']
        for r in rows:
            r = r.strip().rstrip("\\")
            if not r:
                continue
            cells = [c.strip() for c in r.split("&")]
            out.append("  <tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
        out.append("</table>")
        return "\n\n" + "\n".join(out) + "\n\n"
    text = re.sub(r"\\begin\{tabular\}\{([^}]*)\}(.*?)\\end\{tabular\}",
                  _tabular_repl, text, flags=re.DOTALL)

    # Bibliography environment / commands — drop entirely (no bibliography on web)
    text = re.sub(r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}",
                  "", text, flags=re.DOTALL)
    text = re.sub(r"\\bibitem\{[^}]+\}", "", text)
    text = re.sub(r"\\bibliographystyle\{[^}]+\}", "", text)
    text = re.sub(r"\\bibliography\{[^}]+\}", "", text)
    text = re.sub(r"\\nocite\*?\{[^}]*\}", "", text)

    # center / flushleft / flushright — keep inner content
    for env in ("center", "flushleft", "flushright"):
        text = re.sub(r"\\begin\{" + env + r"\}", "", text)
        text = re.sub(r"\\end\{" + env + r"\}", "", text)

    # \begin{proof}…\end{proof} → keep content, mark with header
    text = re.sub(r"\\begin\{proof\}",  r"\n\n<h4>Proof.</h4>\n\n", text)
    text = re.sub(r"\\end\{proof\}",   r"\n\n", text)

    # \begin{theorem}, \begin{definition}, \begin{remark} … keep with header
    for env, label in [("theorem", "Theorem"), ("lemma", "Lemma"),
                       ("proposition", "Proposition"), ("definition", "Definition"),
                       ("remark", "Remark"), ("example", "Example"),
                       ("corollary", "Corollary")]:
        text = re.sub(r"\\begin\{" + env + r"\}", f"\n\n<h4>{label}.</h4>\n\n", text)
        text = re.sub(r"\\end\{" + env + r"\}", "\n\n", text)

    return text


import sys as _sys, os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from svg_render import render_or_fallback, KIND_TIKZ, KIND_MATH


def stash_tikz(text, stash):
    """Pull tikz / feynmandiagram blocks out of the source, replacing them
    with placeholder sentinels so they survive math-stashing and paragraphing.
    The stashed source is later rendered to inline SVG by svg_render."""
    # tikzpicture environment
    pat = re.compile(r"\\begin\{tikzpicture\}(\[[^\]]*\])?(.*?)\\end\{tikzpicture\}",
                     re.DOTALL)

    def tikz_repl(m):
        opts = m.group(1) or ""
        body = m.group(2)
        full_src = f"\\begin{{tikzpicture}}{opts}{body}\\end{{tikzpicture}}"
        idx = len(stash["tikz"])
        stash["tikz"].append(full_src)
        return f"\x00TIKZ{idx}\x00"

    text = pat.sub(tikz_repl, text)

    # standalone \feynmandiagram[...] {...};
    pat2 = re.compile(r"\\feynmandiagram(\[[^\]]*\])?\s*\{(.*?)\}\s*;", re.DOTALL)
    def fdiag_repl(m):
        opts = m.group(1) or ""
        body = m.group(2)
        # Wrap in a tikzpicture so standalone wraps it the same way as inline.
        full_src = f"\\begin{{tikzpicture}}\\feynmandiagram{opts}{{{body}}};\\end{{tikzpicture}}"
        idx = len(stash["tikz"])
        stash["tikz"].append(full_src)
        return f"\x00TIKZ{idx}\x00"
    text = pat2.sub(fdiag_repl, text)

    # Unwrap `$\vcenter{\hbox{TIKZ_PLACEHOLDER}}$` (and similar) — when a
    # figure was embedded inline with math via TeX layout commands, the
    # surrounding `$..$` would otherwise stash it as inline math and produce
    # broken output. Strip those wrappers around bare tikz placeholders.
    def _unwrap_tikz_in_math(t):
        # Iteratively peel surrounding wrappers around a placeholder.
        prev = None
        while prev != t:
            prev = t
            # $ \vcenter { \hbox { TIKZ } } $   (with optional whitespace)
            t = re.sub(
                r"\$\s*(?:\\(?:vcenter|hbox|vbox|mbox|raisebox\{[^}]*\})\s*\{)+\s*"
                r"(\x00TIKZ\d+\x00)"
                r"\s*(?:\})+\s*\$",
                r"\1",
                t,
            )
            # \( \vcenter{\hbox{ TIKZ }} \)
            t = re.sub(
                r"\\\(\s*(?:\\(?:vcenter|hbox|vbox|mbox|raisebox\{[^}]*\})\s*\{)+\s*"
                r"(\x00TIKZ\d+\x00)"
                r"\s*(?:\})+\s*\\\)",
                r"\1",
                t,
            )
            # bare $TIKZ$ or \(TIKZ\)
            t = re.sub(r"\$\s*(\x00TIKZ\d+\x00)\s*\$", r"\1", t)
            t = re.sub(r"\\\(\s*(\x00TIKZ\d+\x00)\s*\\\)", r"\1", t)
        return t
    text = _unwrap_tikz_in_math(text)

    return text


def _tikz_to_svg(src):
    """Render one tikzpicture/feynmandiagram block to an inline-SVG figure.
    On compile failure, show the LaTeX source verbatim as a fallback."""
    safe = src.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    fallback = (
        '<figure class="tikz-source">'
        '<pre aria-label="LaTeX source (compile failed)">'
        f'{safe}'
        '</pre>'
        '<figcaption>Diagram failed to compile; LaTeX source shown above.</figcaption>'
        '</figure>'
    )
    svg = render_or_fallback(src, KIND_TIKZ, fallback)
    if svg.startswith("<figure"):  # fallback HTML
        return svg
    return f'<figure class="tikz-figure">{svg}</figure>'


def restore_tikz(text, stash):
    def repl(m):
        idx = int(m.group(1))
        return _tikz_to_svg(stash["tikz"][idx])
    return re.sub(r"\x00TIKZ(\d+)\x00", repl, text)


def stash_math(text, stash):
    # 0. Pull TikZ figures out FIRST (before anything else touches them)
    text = stash_tikz(text, stash)

    # 1. Pre-strip TeX-only artefacts that don't translate
    text = strip_tex_only_constructs(text)

    # 2. Display environments — walk in source order so equation numbers
    #    come out monotonically.  Previously the env-type loop processed
    #    all `equation` envs first, then `align`, etc., which left mixed
    #    pages with numbering like (1, 23, 2, 3, …).
    env_alt = "|".join(re.escape(e) for e in DISPLAY_ENVS)
    env_pattern = re.compile(
        r"\\begin\{(" + env_alt + r")\}(.*?)\\end\{\1\}",
        re.DOTALL,
    )
    def repl(m):
        env = m.group(1)
        body = m.group(2).strip()
        starred = env.endswith("*")
        # Extract any \label{...} BEFORE we strip them (so we can number)
        label_match = re.search(r"\\label\{([^}]+)\}", body)
        label = label_match.group(1) if label_match else None
        body = re.sub(r"\\label\{[^}]+\}", "", body)

        # Assign a number unless the env is starred (LaTeX convention)
        number = None
        if not starred:
            number = stash.next_eq_number()
            if label:
                stash["labels"][label] = number

        if env.startswith("align"):
            wrap = ("\\begin{aligned}", "\\end{aligned}")
        elif env.startswith("gather"):
            wrap = ("\\begin{gathered}", "\\end{gathered}")
        else:
            wrap = ("", "")

        # ----- Equation containing a TikZ figure: render as flex row -----
        if "\x00TIKZ" in body:
            parts = re.split(r"(\x00TIKZ\d+\x00)", body)
            fragments = []
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    # Strip nested aligned/align/gather wrappers — they
                    # would leak as unmatched \begin / \end into chunks.
                    for env_name in ("aligned", "align", "align*", "gather",
                                      "gathered", "multline", "multline*",
                                      "split"):
                        part = re.sub(
                            r"\\(?:begin|end)\{" + re.escape(env_name) + r"\}",
                            "",
                            part,
                        )
                    # Strip `\\[6pt]`-style row spacing that LaTeX uses
                    # inside align — they leak to text otherwise.
                    part = re.sub(r"\\\\\s*\[[^\]]*\]", "\\\\\\\\", part)
                    # Split by `\\` row separator so each row becomes its
                    # own inline math span; strip `&` alignment markers.
                    rows = re.split(r"\\\\", part)
                    for row in rows:
                        row = row.replace("&", "")
                        # also strip leftover `[6pt]` etc.
                        row = re.sub(r"^\s*\[[^\]]*\]\s*", "", row)
                        row = row.strip().strip("{}").strip()
                        if not row or row in ("=", ".", ",", ":", ";"):
                            continue
                        fragments.append(
                            f'<span class="equation-part">\\({row}\\)</span>'
                        )
                else:
                    # tikz placeholder; will be restored later
                    fragments.append(part)
            row = '\n\n<div class="equation-row">' + "".join(fragments)
            if number is not None:
                row += f'<span class="equation-num">({number})</span>'
            row += '</div>\n\n'
            return row

        # ----- Pure equation: emit \[ ... \tag{N} \] -----
        tag_part = ""
        if number is not None:
            tag_part = f"\\tag{{{number}}}"
        full = wrap[0] + body + wrap[1] + tag_part
        return stash.stash(full, display=True)
    text = env_pattern.sub(repl, text)

    # 2. \[ ... \]
    text = re.sub(r"\\\[(.+?)\\\]",
                  lambda m: stash.stash(m.group(1).strip(), display=True),
                  text, flags=re.DOTALL)

    # 3. $$ ... $$
    text = re.sub(r"\$\$(.+?)\$\$",
                  lambda m: stash.stash(m.group(1).strip(), display=True),
                  text, flags=re.DOTALL)

    # 4. \( ... \)
    text = re.sub(r"\\\((.+?)\\\)",
                  lambda m: stash.stash(m.group(1).strip(), display=False),
                  text, flags=re.DOTALL)

    # 5. $ ... $ (single-dollar inline; greedy-safe with no $$ left)
    #    use a careful pattern that doesn't span across \n\n.
    def inline_dollar_repl(m):
        return stash.stash(m.group(1), display=False)
    text = re.sub(r"\$([^\$\n]+?)\$", inline_dollar_repl, text)

    return text


def transform_text(text, stash=None):
    """Apply structural and formatting LaTeX → HTML transformations on the
    text segments (math regions are already stashed)."""
    # Strip percent-comments (TeX comments), preserving leading whitespace
    text = re.sub(r"(?m)(?<!\\)%.*$", "", text)

    # ── EARLY: extract \begin{figure}…\end{figure} blocks BEFORE we strip
    # \label{} so the figure handler can record figure-number labels for
    # \ref{} resolution.
    #
    # Two cases: figure body contains an \includegraphics (image asset),
    # or it contains a stashed TikZ block (\x00TIKZ%d\x00) — pgfplots,
    # tikz-feynman, or plain tikz wrapped in \begin{figure}. In the
    # second case we keep the placeholder so the tikz-marker pass later
    # turns it into an inline SVG.
    def _early_figure_repl(m):
        body = m.group(1)
        img = re.search(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", body)
        # By the time _early_figure_repl runs, latex_to_html() has already
        # converted \x00TIKZ%d\x00 into <div class="tikz-marker" data-tikz="N"></div>
        # markers; match that form.
        tikz_marker = re.search(
            r'<div class="tikz-marker" data-tikz="\d+"></div>', body)
        cap = re.search(r"\\caption\{(.+?)\}\s*(?:\\label\{[^}]+\})?", body, re.DOTALL)
        label_m = re.search(r"\\label\{([^}]+)\}", body)
        if not img and not tikz_marker:
            return ""
        # Bump the figure counter and capture the label → number mapping
        # so \ref{} / \eqref{} resolve correctly later.
        if stash is not None:
            stash["fig_counter"] = stash.get("fig_counter", 0) + 1
            if label_m:
                stash["labels"][label_m.group(1)] = str(stash["fig_counter"])
        caption_html = cap.group(1).strip() if cap else ""
        alt = re.sub(r"\x00MATH\d+\x00", "", caption_html)
        alt = re.sub(r"\s+", " ", alt).strip()[:120]
        alt = alt.replace('"', "'")

        if img:
            FIG_MAP = {
                "截屏2025-09-03 11.12.36.png": "../assets/path-integral-fig1-spacetime.png",
                "截屏2025-09-03 11.12.36 (1).png": "../assets/path-integral-fig1-spacetime.png",
                "截屏2025-12-06 22.06.22.png": "../assets/path-integral-fig2-slits.png",
                "截屏2025-12-07 14.59.48.png": "../assets/path-integral-fig3-paths.png",
                "截屏2025-12-07 21.55.01.png": "../assets/path-integral-fig4-wick.png",
                "截屏2025-12-08 11.10.24.png": "../assets/path-integral-fig5-cylinder.png",
            }
            src = img.group(1).strip()
            href = FIG_MAP.get(src, f"../assets/{src}")
            inner = f'<img src="{href}" alt="{alt}">'
            if caption_html:
                return f'\n\n<figure>{inner}<figcaption>{caption_html}</figcaption></figure>\n\n'
            return f'\n\n<figure>{inner}</figure>\n\n'

        # tikz-only figure: rewrite the marker to carry the caption as a
        # data attribute. The tikz-marker substitution later reads it and
        # injects a <figcaption> inside the tikz-figure (no nested figures).
        if caption_html:
            # base64-ish encode the caption so it survives quote conflicts:
            # we just escape `&`, `"`, and \n and stash it as a data attr.
            cap_attr = (caption_html
                        .replace("&", "&amp;")
                        .replace('"', "&quot;")
                        .replace("\n", " "))
            return tikz_marker.group(0).replace(
                'data-tikz="', f'data-figcaption="{cap_attr}" data-tikz="'
            )
        return tikz_marker.group(0)
    text = re.sub(r"\\begin\{figure\}\*?(?:\[[^\]]*\])?\s*(.*?)\\end\{figure\}\*?",
                  _early_figure_repl, text, flags=re.DOTALL)

    # \label{...} – drop (handled separately above for figures)
    text = re.sub(r"\\label\{[^}]+\}", "", text)

    # \cite{...} – drop entirely (no bibliography on web)
    text = re.sub(r"\\cite\*?\{[^}]+\}", "", text)

    # \ref{X} / \eqref{X} — resolved later in latex_to_html when the labels
    # map is known. We mark them with sentinels here so they survive the rest
    # of text-transforms.
    text = re.sub(r"\\eqref\{([^}]+)\}", lambda m: f"\x00EQREF[{m.group(1)}]\x00", text)
    text = re.sub(r"\\ref\{([^}]+)\}",   lambda m: f"\x00REF[{m.group(1)}]\x00", text)

    # \footnote{...} – inline parentheses
    text = re.sub(r"\\footnote\{(.+?)\}", r" (\1)", text, flags=re.DOTALL)

    # subsection / subsubsection / paragraph (balanced braces — titles can
    # contain inline math like $\frac{1}{2}$)
    text = _balanced_arg_replace(text, "subsection",   lambda a: f"\n\n<H3>{a}</H3>\n\n")
    text = _balanced_arg_replace(text, "subsubsection",lambda a: f"\n\n<H4>{a}</H4>\n\n")
    text = _balanced_arg_replace(text, "paragraph",    lambda a: f"\n\n<H5>{a}</H5>\n\n")

    # \textbf{...}, \emph{...}, \textit{...}, \underline{...}
    text = _balanced_arg_replace(text, "textbf",   lambda a: f"<strong>{a}</strong>")
    text = _balanced_arg_replace(text, "emph",     lambda a: f"<em>{a}</em>")
    text = _balanced_arg_replace(text, "textit",   lambda a: f"<em>{a}</em>")
    text = _balanced_arg_replace(text, "underline",lambda a: f"<u>{a}</u>")

    # \href{url}{text} -> link
    text = re.sub(r"\\href\{([^}]+)\}\{([^}]+)\}",
                  lambda m: f'<a href="{m.group(1)}">{m.group(2)}</a>', text)

    # Lists: itemize / enumerate / description.
    # Handle optional [label=...] / [a)] options after \begin{...}.
    def list_repl(env_name, tag):
        pat = re.compile(
            r"\\begin\{" + env_name + r"\}(?:\[[^\]]*\])?"
            r"(.*?)\\end\{" + env_name + r"\}",
            re.DOTALL,
        )
        def transform(m):
            body = m.group(1)
            # \item may have a [...] label; we drop the label spec for now
            items = re.split(r"\\item\s*(?:\[[^\]]*\])?\s*", body)
            items = [i.strip() for i in items if i.strip()]
            lis = "".join(f"\n  <li>{i}</li>" for i in items)
            return f"\n\n<{tag}>{lis}\n</{tag}>\n\n"
        return pat, transform
    p, t = list_repl("itemize", "ul"); text = p.sub(t, text)
    p, t = list_repl("enumerate", "ol"); text = p.sub(t, text)
    p, t = list_repl("description", "ul"); text = p.sub(t, text)

    # quote / quotation
    p, t = list_repl("quote", "blockquote"); text = p.sub(t, text)

    text = re.sub(r"\\begin\{table\}.*?\\end\{table\}", "", text, flags=re.DOTALL)
    text = re.sub(r"\\centering", "", text)
    # any leftover \includegraphics outside figure → standalone figure
    text = re.sub(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}",
                  lambda m: f'\n\n<figure><img src="../assets/{m.group(1).strip()}" alt=""></figure>\n\n',
                  text)
    text = re.sub(r"\\caption\{[^}]+\}", "", text)

    # remove residual single-line LaTeX commands that don't translate
    text = re.sub(r"\\noindent\b\s*", "", text)
    text = re.sub(r"\\medskip\b\s*", "", text)
    text = re.sub(r"\\bigskip\b\s*", "", text)
    text = re.sub(r"\\smallskip\b\s*", "", text)
    # \hfill is layout-only — strip in prose. (In math it'd never reach
    # this stage since math regions are already stashed.)
    text = re.sub(r"\\hfill\b\s*", "", text)
    # \, is a thin space. In math (already stashed) MathJax handles it.
    # In prose, it's a non-breaking thin space → use &nbsp; so the user
    # gets the right visual ("100\,atm" → "100 atm").
    text = text.replace(r"\,", " ")
    # \: and \; are also thin/medium spaces in TeX; same treatment.
    text = re.sub(r"\\[:;!]", " ", text)
    # font-size / font-style declarative commands (LARGE, large, Huge, ...)
    text = re.sub(r"\\(?:LARGE|Large|large|small|Huge|huge|tiny|footnotesize|normalsize|scriptsize|bf|it|sl|sc|rm|tt|sf)\b\s*",
                  "", text)
    # counter manipulation
    text = re.sub(r"\\setcounter\{[^}]+\}\{[^}]+\}", "", text)
    text = re.sub(r"\\addtocounter\{[^}]+\}\{[^}]+\}", "", text)
    # TeX comments and font-family selectors
    text = re.sub(r"\\fontsize\{[^}]*\}\{[^}]*\}\\selectfont", "", text)
    text = re.sub(r"\\selectfont\b\s*", "", text)
    # cross-reference commands we don't model
    text = re.sub(r"\\(?:thanks|date|author|maketitle|tableofcontents)\b\s*(\{[^}]*\})?", "", text)
    text = re.sub(r"\\title\{[^}]+\}", "", text)

    # ~ → non-breaking space
    text = text.replace("~", "&nbsp;")

    # `` and '' → curly quotes
    text = text.replace("``", "&ldquo;").replace("''", "&rdquo;")
    # `x' → ‘x’
    text = re.sub(r"(?<!\\)`([^']+)'", r"&lsquo;\1&rsquo;", text)

    # Restore <H3> / <H4> / <H5> sentinels (uppercased to avoid clashing
    # with anything that might already be in prose)
    text = text.replace("<H3>", "<h3>").replace("</H3>", "</h3>")
    text = text.replace("<H4>", "<h4>").replace("</H4>", "</h4>")
    text = text.replace("<H5>", "<h5>").replace("</H5>", "</h5>")

    # Paragraphisation: split on blank lines.
    paragraphs = re.split(r"\n\s*\n", text)
    out = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        # If the chunk is (or starts with / ends with) a block-level element,
        # leave it alone — never wrap block-level tags inside <p>.
        if re.match(r"^<(h[1-6]|ul|ol|blockquote|figure|hr|div|p|aside|article|section|table)\b", p, re.I):
            out.append(p)
            continue
        if re.match(r"^</(aside|figure|div|section|article|table)\b", p, re.I):
            out.append(p)
            continue
        # Otherwise wrap in <p>
        out.append(f"<p>{p}</p>")
    return "\n\n".join(out)


def latex_to_html(body, stash=None):
    """Convert a chunk of LaTeX to HTML. Optionally accept a shared MathStash
    so equation numbering accumulates across multiple sections of the same
    page (this is what we want for whole-document conversions)."""
    if stash is None:
        stash = MathStash()
    body = stash_math(body, stash)
    # Replace tikz placeholders with block-level <div> markers so the
    # paragraphizer treats them as standalone.  Two passes: placeholders
    # *inside* an equation-row stay inline (no surrounding newlines, so
    # the paragraphizer doesn't split the row across <p> boundaries —
    # which previously produced malformed `<p>...</div></p>` markup);
    # everything else gets newlines so it becomes its own block.
    def _eqrow_inline_tikz(m):
        inner = re.sub(
            r"\x00TIKZ(\d+)\x00",
            r'<div class="tikz-marker" data-tikz="\1"></div>',
            m.group(1),
        )
        return '<div class="equation-row">' + inner + '</div>'
    body = re.sub(
        r'<div class="equation-row">(.*?)</div>',
        _eqrow_inline_tikz, body, flags=re.DOTALL,
    )
    body = re.sub(r"\x00TIKZ(\d+)\x00",
                  r'\n\n<div class="tikz-marker" data-tikz="\1"></div>\n\n',
                  body)
    body = transform_text(body, stash=stash)
    body = stash.restore(body)
    # Equations containing \wick{...} can't be rendered live by MathJax —
    # the simpler-wick package is LaTeX-only and the polyfill at best draws
    # a single overbrace. Pre-render those whole equations to inline SVG
    # via lualatex so multi-pair contraction arcs stay distinct.
    def _wick_to_svg(m):
        inner = m.group(1)
        # stash.restore HTML-escaped < > & inside math; un-escape before
        # handing the body to LaTeX.
        for src, repl in (("&lt;", "<"), ("&gt;", ">"), ("&amp;", "&")):
            inner = inner.replace(src, repl)
        fallback = f'\\[{m.group(1)}\\]'    # leave it for MathJax to attempt
        svg = render_or_fallback(inner, KIND_MATH, fallback)
        if svg.startswith("\\["):
            return svg
        return f'<figure class="wick-figure">{svg}</figure>'
    # Match \[...\\wick...\]. The body may contain literal `[X]` (e.g.
    # commutators) — those are bare brackets, not display-math delimiters,
    # so we use non-greedy `.*?` between \[ and \\] to skip over them.
    body = re.sub(
        r'\\\[((?:(?!\\\]).)*?\\wick(?:(?!\\\]).)*?)\\\]',
        _wick_to_svg, body, flags=re.DOTALL,
    )
    # Substitute tikz markers with the real figures. If the marker carries
    # a data-figcaption (set by _early_figure_repl when the diagram came
    # from a \begin{figure}...\caption{...}\end{figure} block), inject the
    # caption inside the rendered tikz-figure rather than as a sibling.
    def _tikz_marker_repl(m):
        idx = int(m.group("idx"))
        cap = m.group("cap")
        figure_html = render_tikz_one(stash, idx)
        if cap:
            cap = (cap.replace("&quot;", '"').replace("&amp;", "&"))
            figure_html = figure_html.replace(
                "</figure>", f"<figcaption>{cap}</figcaption></figure>", 1)
        return figure_html
    body = re.sub(
        r'<div class="tikz-marker"'
        r'(?: data-figcaption="(?P<cap>[^"]*)")?'
        r' data-tikz="(?P<idx>\d+)"></div>',
        _tikz_marker_repl,
        body,
    )
    # Resolve \eqref{} / \ref{} sentinels using the labels map collected
    # during equation / figure processing. Unknown labels: strip common
    # `fig:`, `eq:`, `sec:` prefixes so they show as a clean fallback
    # instead of leaking the raw key.
    def _clean_unmapped(lab):
        return re.sub(r"^(?:fig|eq|sec|tbl|tab|app|chap|ch):", "", lab)
    def eqref_repl(m):
        lab = m.group(1)
        n = stash["labels"].get(lab)
        return f"({n})" if n else f"({_clean_unmapped(lab)})"
    def ref_repl(m):
        lab = m.group(1)
        n = stash["labels"].get(lab)
        return n if n else _clean_unmapped(lab)
    body = re.sub(r"\x00EQREF\[([^\]]+)\]\x00", eqref_repl, body)
    body = re.sub(r"\x00REF\[([^\]]+)\]\x00",   ref_repl,   body)
    # tidy: collapse 3+ newlines
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


def render_tikz_one(stash, idx):
    return _tikz_to_svg(stash["tikz"][idx])


# ----------------------------------------------------------------------
# Page template
# ----------------------------------------------------------------------

def render_page(**fields):
    """Substitute @@KEY@@ sentinels in PAGE_TEMPLATE. Avoids str.format which
    chokes on { } that legitimately appear in MathJax macro definitions."""
    fields.setdefault("toc", "")           # default empty TOC
    out = PAGE_TEMPLATE
    for k, v in fields.items():
        out = out.replace("@@" + k.upper() + "@@", v)
    return out


def slugify(s):
    s = re.sub(r"<[^>]+>", "", s)             # strip any html
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    s = re.sub(r"[\s_]+", "-", s)
    return s or "section"


def build_toc_and_inject_ids(body_html):
    """Walk h2/h3 headings in `body_html`, assign unique slug ids in-place,
    and return (body_with_ids, toc_html). Returns ('', body_html) if the page
    is too short to need a TOC (≤1 heading)."""
    seen = {}
    headings = []   # list of (level, slug, title_html)

    # Pattern: <h2>Title</h2> or <h2 id="...">Title</h2>
    def repl(m):
        level = int(m.group(1))
        existing_attrs = m.group(2) or ""
        title = m.group(3)
        # if id already present, use it
        idm = re.search(r'id="([^"]+)"', existing_attrs)
        if idm:
            sid = idm.group(1)
            new_attrs = existing_attrs
        else:
            base = slugify(title)
            sid = base
            n = 1
            while sid in seen:
                n += 1
                sid = f"{base}-{n}"
            new_attrs = (existing_attrs + f' id="{sid}"').strip()
            new_attrs = " " + new_attrs if not new_attrs.startswith(" ") else new_attrs
        seen[sid] = True
        headings.append((level, sid, title))
        return f"<h{level} {new_attrs.strip()}>{title}</h{level}>"

    body_with_ids = re.sub(
        r"<h([23])(\s[^>]*)?>(.*?)</h\1>",
        repl,
        body_html,
        flags=re.DOTALL,
    )

    # Build TOC
    if len(headings) < 2:
        return body_with_ids, ""

    toc_lines = ['<nav class="note__toc" aria-label="Contents">',
                 '  <div class="note__toc-label">On this page</div>',
                 '  <ol class="note__toc-list">']
    current_level = 2
    for level, sid, title in headings:
        if level == 2:
            toc_lines.append(f'    <li class="toc-h2"><a href="#{sid}">{title}</a></li>')
        else:
            toc_lines.append(f'    <li class="toc-h3"><a href="#{sid}">{title}</a></li>')
    toc_lines.append('  </ol>')
    toc_lines.append('</nav>')
    return body_with_ids, "\n".join(toc_lines)


PAGE_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>@@TITLE@@ — Yucheng (Luca) Jin</title>
<meta name="description" content="@@TITLE@@. Source: @@SOURCE_SHORT@@.">

<link rel="icon" type="image/svg+xml" href="../assets/favicon.svg">

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">

<link rel="stylesheet" href="../styles.css">

<script src="../assets/theme.js"></script>
<script src="../assets/font-size.js"></script>

<!-- MathJax with custom macros mirroring the original .tex preamble -->
<script>
window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    displayMath: [['$$', '$$'], ['\\[', '\\]']],
    packages: {'[+]': ['physics', 'boldsymbol', 'cancel', 'ams', 'configmacros', 'mathtools']},
    macros: {
      R: '\\mathbb{R}',
      C: '\\mathbb{C}',
      Z: '\\mathbb{Z}',
      N: '\\mathbb{N}',
      Q: '\\mathbb{Q}',
      A: '\\mathcal{A}',
      Lagrangian: '\\mathcal{L}',
      Cdot: '\\boldsymbol{\\cdot}',
      Tr: '\\operatorname{Tr}',
      slashed: ['{\\not{#1}}', 1],
      // Wick contraction: top brace connector over the contracted pair —
      // closer to the standard physics notation than a plain overline.
      wick:    ['{\\overbrace{#1}^{\\!\\!}}', 1],
      c:       ['{#1}', 1],
      mathds:  ['\\mathbb{#1}', 1],
      Tilde:   ['\\tilde{#1}', 1],
      // siunitx polyfill — \si{K}, \si{m\,s^{-1}} etc. should render
      // the unit in upright math text, like \mathrm{X}. Doesn't try
      // to mimic the full siunitx unit-formatting machinery; just
      // unblocks the common bare-unit case in TDSP problems.
      si: ['\\,\\mathrm{#1}', 1],
      SI: ['#1\\,\\mathrm{#2}', 2]
      // \tensor{base}{indices} is rewritten to base^a{}_b in
      // build/tex_to_html.py:_rewrite_tensor before MathJax sees it,
      // so no runtime macro is needed here. The empty-group trick is
      // what makes MathJax kern the indices into separate columns.
    }
  },
  loader: { load: ['[tex]/physics', '[tex]/boldsymbol', '[tex]/cancel', '[tex]/ams', '[tex]/configmacros', '[tex]/mathtools'] }
};
</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
</head>
<body>

<header class="topbar">
  <a href="../index.html" class="topbar__brand">Yucheng (Luca) Jin <small>MSci · Imperial</small></a>
  <nav class="topbar__nav">
    <a href="../index.html">About</a>
    <a href="../notes.html" class="is-active">Notes</a>
    <a href="../research.html">Research</a>
    <a href="mailto:luca.jin@outlook.com">Contact</a>
    <button class="font-toggle" type="button" data-font-size="dec" aria-label="Decrease font size" title="Decrease font size">A<span class="font-toggle__small">−</span></button>
    <button class="font-toggle" type="button" data-font-size="inc" aria-label="Increase font size" title="Increase font size">A<span class="font-toggle__large">+</span></button>
    <button class="theme-toggle" type="button" data-theme-toggle aria-label="Switch to dark theme" title="Toggle theme">
      <svg class="icon-moon" viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z"/></svg>
      <svg class="icon-sun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>
    </button>
  </nav>
</header>

<main class="note">

  <div class="note__breadcrumb">
    <a href="../notes.html">Notes</a> &nbsp;·&nbsp; @@BREADCRUMB@@
  </div>

  <h1 class="note__title">@@TITLE@@</h1>
  <p class="note__subtitle">Source: @@SOURCE_LONG@@</p>

  @@TOC@@

  <article class="note__body">
@@BODY@@
  </article>

  <hr class="ornament-rule">

  <p style="font-style:italic; color:var(--muted); font-family:var(--display); text-align:center;">
    <a href="../notes.html">← Back to all notes</a>
  </p>

</main>

<footer class="footer">
  <span>© 2026 Yucheng (Luca) Jin</span>
  <span>
    <a href="../index.html">About</a> ·
    <a href="../notes.html">Notes</a> ·
    <a href="mailto:luca.jin@outlook.com">Email</a>
  </span>
</footer>

</body>
</html>
"""


# ----------------------------------------------------------------------
# QFT Schwartz: convert each \subsection in QFTschwartz.tex into one page,
# but reuse the chapter groupings already in notes.html.
# ----------------------------------------------------------------------

# New whole-document files: each compiles into a single page with TOC
WHOLE_FILE_PAGES = [
    # (tex_file, slug, title, breadcrumb, source_long)
    ("11dsupergravity.tex", "psi-11d-supergravity",
        "11-Dimensional Supergravity",
        "General Relativity &amp; Beyond · PSI Strings PS1 Q3",
        "Perimeter Scholars International, Strings &amp; AdS/CFT, Problem Sheet 1, Question 3."),
    ("BransDicke.tex", "gr-brans-dicke",
        "Brans–Dicke Theory",
        "General Relativity &amp; Beyond · Tong GR PS3 Q2",
        "D. Tong, <em>General Relativity</em>, Problem Sheet 3, Question 2."),
    ("Correlation_functions_in_QM.tex", "psi-correlation-functions-qm",
        "Correlation Functions in Quantum Mechanics",
        "General Relativity &amp; Beyond · PSI QFT II PS1",
        "Perimeter Scholars International, QFT II, Problem Sheet 1."),
    ("DTQFTPS1.tex", "tong-qft-ps1",
        "Tong QFT — Problem Sheet 1",
        "Quantum Field Theory · Tong QFT PS1",
        "D. Tong, <em>Quantum Field Theory</em>, Problem Sheet 1 (Lorentz / symmetries)."),
    ("DTQFTPS2.tex", "tong-qft-ps2",
        "Tong QFT — Problem Sheet 2",
        "Quantum Field Theory · Tong QFT PS2",
        "D. Tong, <em>Quantum Field Theory</em>, Problem Sheet 2 (canonical quantization)."),
    ("DTQFTPS3.tex", "tong-qft-ps3",
        "Tong QFT — Problem Sheet 3",
        "Quantum Field Theory · Tong QFT PS3",
        "D. Tong, <em>Quantum Field Theory</em>, Problem Sheet 3 (Dirac fields)."),
]


SCHWARTZ_GROUPS = [
    ("schwartz-classical-field",
        "Classical Field Theory",
        "Quantum Field Theory · Schwartz Ch. 1–3",
        "M. D. Schwartz, <em>Quantum Field Theory and the Standard Model</em>, Chapters 1–3.",
        ["The Euler-Lagrange Equations", "Noether's Theorem", "Green's Functions"]),
    ("schwartz-second-quantization",
        "Second Quantization &amp; LSZ Reduction",
        "Quantum Field Theory · Schwartz Ch. 2–6",
        "M. D. Schwartz, <em>Quantum Field Theory and the Standard Model</em>, Chapters 2–6.",
        ["Quantum Mechanical Harmonic Oscillator", "Second Quantization",
         "$S$-matrix", "Cross Sections",
         "The LSZ reduction Formula", "The Feynman Propagator",
         "Lagrangian Derivation", "Hamiltonian Derivation", "Momentum-Space Feynman Rules"]),
    ("schwartz-spin-1",
        "Spin 1, Gauge Invariance, Photon Propagator",
        "Quantum Field Theory · Schwartz Ch. 8–9",
        "M. D. Schwartz, <em>Quantum Field Theory and the Standard Model</em>, Chapters 8–9.",
        ["Unitary Representation of Poincaré Group", "Embedding Particles into Fields",
         "Covariant Derivatives", "Quantisation and the Ward Identity", "The Photon Propagator",
         "Quantizing Complex Scalar Fields", "Feynman Rules for Scalar QED",
         "Scattering in Scalar QED", "Ward Identity and Gauge Invariance",
         "Lorentz Invariance and Charge Conservation"]),
    ("schwartz-spinors",
        "Spinors, Dirac Equation, CPT",
        "Quantum Field Theory · Schwartz Ch. 10–11",
        "M. D. Schwartz, <em>Quantum Field Theory and the Standard Model</em>, Chapters 10–11.",
        ["Representations of the Lorentz Group", "Spinor Representations", "Dirac Matrices",
         "Coupling with the Photon Fields", "The Meaning of spin", "Majorana and Weyl Fermions",
         "Spin, Helicity and Chirality", "Solving the Dirac Equation", "Majorana Fermions",
         "Charge Conjugation", "Parity", "Time Reversal"]),
    ("schwartz-qed-tree",
        "QED Tree Amplitudes",
        "Quantum Field Theory · Schwartz Ch. 13",
        "M. D. Schwartz, <em>Quantum Field Theory and the Standard Model</em>, Chapter 13.",
        ["QED Feynman Rules", "matrix Identities",
         "$e^+e^-\\to \\mu^+\\mu^-$", "Rutherford Scattering"]),
    ("schwartz-path-integrals",
        "Path Integrals (in QFT)",
        "Quantum Field Theory · Schwartz Ch. 14",
        "M. D. Schwartz, <em>Quantum Field Theory and the Standard Model</em>, Chapter 14.",
        ["Path Integral"]),
]


def extract_subsections_by_titles(text, title_substrings):
    """Return a list of (title, body) for each subsection in text whose title
    contains any of the given lowercase substrings, in document order."""
    matches = _find_balanced_command_args(text, "subsection")
    out = []
    for i, (cstart, cend, title_raw) in enumerate(matches):
        title_lc = title_raw.lower()
        if not any(sub.lower() in title_lc for sub in title_substrings):
            continue
        start = cend
        end = matches[i + 1][0] if i + 1 < len(matches) else len(text)
        next_section = re.search(r"\\section\*?\{", text[start:end])
        if next_section:
            end = start + next_section.start()
        out.append((title_raw, text[start:end]))
    return out


def extract_section_body(text, section_title):
    """Find the \\section{...} matching `section_title` (substring, case-insens)
    and return its body up to the next \\section or \\end{document}."""
    needle = section_title.lower()
    matches = _find_balanced_command_args(text, "section")
    for i, (cstart, cend, title) in enumerate(matches):
        if needle in title.lower():
            start = cend
            end = matches[i + 1][0] if i + 1 < len(matches) else len(text)
            end_doc = re.search(r"\\end\{document\}", text[start:end])
            if end_doc:
                end = start + end_doc.start()
            return title, text[start:end]
    return None, None


def write_schwartz_pages(schwartz_text):
    written = 0
    for slug, page_title, breadcrumb, source_long, picks in SCHWARTZ_GROUPS:
        # Special case: schwartz-path-integrals matches the whole \section{Path Integral}
        if slug == "schwartz-path-integrals":
            stitle, body = extract_section_body(schwartz_text, "Path Integral")
            if body is None:
                print(f"  warn: section not found for {slug}")
                continue
            body_html = latex_to_html(body)
            path = os.path.join(OUT, f"{slug}.html")
            full_body = f"<h2>{stitle}</h2>\n\n{body_html}"
            full_body, toc_html = build_toc_and_inject_ids(full_body)
            with open(path, "w") as f:
                f.write(render_page(
                    title=page_title,
                    source_short=source_long.replace("<em>", "").replace("</em>", "").split(",")[0],
                    source_long=source_long,
                    breadcrumb=breadcrumb,
                    body=full_body,
                    toc=toc_html,
                ))
            written += 1
            print(f"  wrote {slug}.html  (section: {stitle})")
            continue

        subs = extract_subsections_by_titles(schwartz_text, picks)
        if not subs:
            print(f"  warn: no subsections matched for {slug}")
            continue
        # Share one stash so labels resolve across subsections, but reset the
        # equation counter at each new subsection so numbering restarts at (1)
        # for every topic.
        shared = MathStash()
        body_chunks = []
        for sub_title, sub_body in subs:
            shared.reset_eq_counter()
            body_chunks.append(f"\n<h2>{sub_title}</h2>\n\n"
                               + latex_to_html(sub_body, stash=shared))
        body_html = "\n".join(body_chunks)
        body_html, toc_html = build_toc_and_inject_ids(body_html)
        path = os.path.join(OUT, f"{slug}.html")
        with open(path, "w") as f:
            f.write(render_page(
                title=page_title,
                source_short=source_long.replace("<em>", "").replace("</em>", "").split(",")[0],
                source_long=source_long,
                breadcrumb=breadcrumb,
                body=body_html,
                toc=toc_html,
            ))
        written += 1
        print(f"  wrote {slug}.html  ({len(subs)} subsections)")
    return written


def write_essay_page(tex_path, slug, title, breadcrumb, source_long):
    """Convert a full-document essay (multi-section) into one HTML page,
    preserving the original section structure."""
    with open(tex_path) as f:
        text = f.read()
    # Skip everything before \section{Introduction} (or the first \section)
    first = re.search(r"\\section\*?\{", text)
    if not first:
        print(f"  warn: no \\section in {tex_path}")
        return
    text = text[first.start():]
    # Stop at \end{document}
    end = re.search(r"\\end\{document\}", text)
    if end:
        text = text[:end.start()]
    # Convert sections to <h2> by walking
    matches = _find_balanced_command_args(text, "section")
    out_chunks = []
    shared = MathStash()
    for i, (cstart, cend, sec_title) in enumerate(matches):
        sec_title = sec_title.strip()
        start = cend
        end_pos = matches[i + 1][0] if i + 1 < len(matches) else len(text)
        sec_body = text[start:end_pos]
        shared.reset_eq_counter()
        out_chunks.append(f"<h2>{sec_title}</h2>\n\n"
                          + latex_to_html(sec_body, stash=shared))
    body_html = "\n\n".join(out_chunks)
    body_html, toc_html = build_toc_and_inject_ids(body_html)
    out_path = os.path.join(OUT, f"{slug}.html")
    with open(out_path, "w") as f:
        f.write(render_page(
            title=title,
            breadcrumb=breadcrumb,
            source_short=source_long.replace("<em>", "").replace("</em>", "").split(",")[0],
            source_long=source_long,
            body=body_html,
            toc=toc_html,
        ))
    print(f"  wrote {slug}.html  (essay: {len(matches)} sections)")


def write_final_project(qftsoln_text):
    """Extract the \\section{Final Project: ...} block and convert to peskin-final.html."""
    title, body = extract_section_body(qftsoln_text, "Final Project")
    if body is None:
        print("  warn: Final Project section not found")
        return
    body_html = latex_to_html(body)
    body_html, toc_html = build_toc_and_inject_ids(body_html)
    page_title = title.strip()
    breadcrumb = "Quantum Field Theory · Peskin Final Project"
    source_long = "Peskin &amp; Schroeder, <em>An Introduction to Quantum Field Theory</em>, end-of-book final project."
    out_path = os.path.join(OUT, "peskin-final.html")
    with open(out_path, "w") as f:
        f.write(render_page(
            title=page_title,
            breadcrumb=breadcrumb,
            source_short="Peskin & Schroeder",
            source_long=source_long,
            body=body_html,
            toc=toc_html,
        ))
    print(f"  wrote peskin-final.html  (section: {page_title})")


def write_whole_file_page(tex_path, slug, title, breadcrumb, source_long):
    """Convert a whole .tex file (after \\begin{document}) into a single HTML
    page, treating \\section and \\subsection as <h2>/<h3>."""
    with open(tex_path) as f:
        text = f.read()
    # Skip preamble: start at first \section if present, otherwise at \begin{document}
    first_sec = re.search(r"\\section\*?\{", text)
    begin_doc = re.search(r"\\begin\{document\}", text)
    if first_sec:
        text = text[first_sec.start():]
    elif begin_doc:
        text = text[begin_doc.end():]
    end = re.search(r"\\end\{document\}", text)
    if end:
        text = text[:end.start()]

    # For PS files (DTQFTPS1, etc.) the structure is one outer \section with
    # many \subsection topics. We want equation numbers to RESTART at each
    # \subsection, so we promote subsections to <h2> in those cases.
    sub_count = len(re.findall(r"\\subsection\*?\{", text))
    sec_count = len(re.findall(r"\\section\*?\{",    text))
    promote_subsections = (sec_count == 1 and sub_count > 1)

    shared = MathStash()
    out_chunks = []

    if promote_subsections:
        matches = _find_balanced_command_args(text, "subsection")
        if not matches:
            out_chunks.append(latex_to_html(text, stash=shared))
        else:
            pre = text[:matches[0][0]]
            pre = re.sub(r"\\section\*?\{[^}]+\}", "", pre).strip()
            if pre:
                out_chunks.append(latex_to_html(pre, stash=shared))
            for i, (cstart, cend, sub_title) in enumerate(matches):
                sub_title = sub_title.strip()
                display = re.sub(r"\s*\([^)]*\)\s*$", "", sub_title).strip() or sub_title
                start = cend
                end_pos = matches[i + 1][0] if i + 1 < len(matches) else len(text)
                sub_body = text[start:end_pos]
                shared.reset_eq_counter()
                out_chunks.append(f"<h2>{display}</h2>\n\n"
                                  + latex_to_html(sub_body, stash=shared))
    else:
        matches = _find_balanced_command_args(text, "section")
        if not matches:
            out_chunks.append(latex_to_html(text, stash=shared))
        else:
            pre = text[:matches[0][0]].strip()
            if pre:
                out_chunks.append(latex_to_html(pre, stash=shared))
            for i, (cstart, cend, sec_title) in enumerate(matches):
                sec_title = sec_title.strip()
                display = re.sub(r"\s*\([^)]*\)\s*$", "", sec_title).strip() or sec_title
                start = cend
                end_pos = matches[i + 1][0] if i + 1 < len(matches) else len(text)
                sec_body = text[start:end_pos]
                shared.reset_eq_counter()
                out_chunks.append(f"<h2>{display}</h2>\n\n"
                                  + latex_to_html(sec_body, stash=shared))
    body_html = "\n\n".join(out_chunks)
    body_html, toc_html = build_toc_and_inject_ids(body_html)
    out_path = os.path.join(OUT, f"{slug}.html")
    with open(out_path, "w") as f:
        f.write(render_page(
            title=title,
            breadcrumb=breadcrumb,
            source_short=source_long.replace("<em>", "").replace("</em>", "").split(",")[0],
            source_long=source_long,
            body=body_html,
            toc=toc_html,
        ))
    n = len(matches) if 'matches' in dir() else 1
    print(f"  wrote {slug}.html  ({n} topic{'s' if n != 1 else ''})")


def main():
    # Per-subsection pages
    for tex_file, jobs in JOBS:
        path = os.path.join(TEX, tex_file)
        with open(path) as f:
            text = f.read()
        for needle, slug, breadcrumb, source_long in jobs:
            title, body = extract_subsection(text, needle)
            if body is None:
                print(f"  warn: not found in {tex_file}: {needle!r}")
                continue
            # Strip parenthetical "(...)" attribution from the title
            clean_title = re.sub(r"\s*\([^)]*\)\s*$", "", title).strip()
            html_body = latex_to_html(body)
            html_body, toc_html = build_toc_and_inject_ids(html_body)
            out_path = os.path.join(OUT, f"{slug}.html")
            with open(out_path, "w") as f:
                f.write(render_page(
                    title=clean_title,
                    breadcrumb=breadcrumb,
                    source_short=source_long.replace("<em>", "").replace("</em>", "").split(",")[0],
                    source_long=source_long,
                    body=html_body,
                    toc=toc_html,
                ))
            print(f"  wrote {slug}.html")

    # Schwartz multi-section pages
    schwartz_path = os.path.join(TEX, "QFTschwartz.tex")
    with open(schwartz_path) as f:
        schwartz_text = f.read()
    write_schwartz_pages(schwartz_text)

    # Path Integral essay (full document, original prose)
    write_essay_page(
        os.path.join(TEX, "quantumEssay.tex"),
        "path-integral",
        "Path Integrals and the Quantum–Statistical Correspondence",
        "Long-form essay · Imperial Year-2 Quantum Physics",
        "Yucheng (Luca) Jin, Year 2 Quantum Physics essay (Imperial College London, 2025).",
    )

    # Peskin final project
    qftsoln_path = os.path.join(TEX, "QFTsoln.tex")
    with open(qftsoln_path) as f:
        qftsoln_text = f.read()
    write_final_project(qftsoln_text)

    # New whole-document pages (Tong PS1/2/3, Brans-Dicke, 11d sugra, PSI corr)
    for tex_file, slug, title, breadcrumb, source_long in WHOLE_FILE_PAGES:
        write_whole_file_page(
            os.path.join(TEX, tex_file),
            slug, title, breadcrumb, source_long,
        )

    print("done")


if __name__ == "__main__":
    main()
