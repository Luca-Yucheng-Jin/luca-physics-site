r"""
feynman_convert.py — convert tikz-feynman blocks to plain TikZ that TikZJax
can render. See implementation comments for details.
"""

import re
from collections import OrderedDict


# ----- Position vocabulary ------------------------------------------------

POSITION_VECTORS = {
    "right":           (1.6, 0),
    "left":           (-1.6, 0),
    "above":          (0, 1.4),
    "below":          (0, -1.4),
    "above right":    (1.4, 1.0),
    "above left":    (-1.4, 1.0),
    "below right":    (1.4, -1.0),
    "below left":    (-1.4, -1.0),
}


def _balanced_brace_match(s, start):
    """Given `s` and the index of an opening `{`, return the index just past
    the matching `}`, or -1 if not balanced."""
    if start >= len(s) or s[start] != "{":
        return -1
    depth = 1
    j = start + 1
    while j < len(s) and depth > 0:
        if s[j] == "{": depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return j + 1
        j += 1
    return -1


def _extract_particle_label(attrs):
    """Pull the `particle=...` value out of an attrs string. Returns the
    bare TeX expression (no surrounding $...$ or \\(...\\) delimiters); the
    caller wraps the result in $...$ when it emits a TikZ node label."""
    m = re.search(r"particle\s*=\s*", attrs)
    if not m:
        return None
    j = m.end()
    raw = None
    if j < len(attrs) and attrs[j] == "{":
        end = _balanced_brace_match(attrs, j)
        if end > 0:
            raw = attrs[j + 1:end - 1]
    elif attrs[j:j + 2] == "\\(":
        end = attrs.find("\\)", j)
        if end > 0:
            raw = attrs[j + 2:end]
    if raw is None:
        end = attrs.find(",", j)
        if end < 0: end = len(attrs)
        raw = attrs[j:end].strip()
    raw = raw.strip()
    # Strip surrounding math delimiters $...$ or \(...\) if present.
    if raw.startswith("$") and raw.endswith("$"):
        raw = raw[1:-1].strip()
    if raw.startswith("\\(") and raw.endswith("\\)"):
        raw = raw[2:-2].strip()
    return raw


def parse_pos_spec(spec):
    """Parse `right=of a` / `above right=of a` / `right=1cm of a, xshift=...`
    Returns (anchor_name, dx, dy) or None if unparseable."""
    if spec is None:
        return None
    s = spec.strip()
    # Look for "<dir>=of <anchor>" or "<dir>=<dist> of <anchor>"
    m = re.search(r"(above|below)\s+(left|right)\s*=\s*(?:[^,]*?\s+)?of\s+([A-Za-z0-9_]+)", s)
    if m:
        d1, d2 = m.group(1), m.group(2)
        dx, dy = POSITION_VECTORS[f"{d1} {d2}"]
        return (m.group(3), dx, dy)
    m = re.search(r"(above|below|left|right)\s*=\s*(?:[^,]*?\s+)?of\s+([A-Za-z0-9_]+)", s)
    if m:
        dx, dy = POSITION_VECTORS[m.group(1)]
        return (m.group(2), dx, dy)
    return None


# ----- Vertex / edge data classes -----------------------------------------

class Vertex:
    __slots__ = ("name", "label", "pos_spec", "x", "y")
    def __init__(self, name, label=None, pos_spec=None, x=None, y=None):
        self.name = name
        self.label = label
        self.pos_spec = pos_spec
        self.x = x
        self.y = y


# ----- Pattern A: explicit \vertex declarations ---------------------------

def parse_explicit_vertices(src):
    """Return OrderedDict of name -> Vertex from \\vertex declarations.
    The label argument may contain nested braces (e.g. {$e^{+}$}) so we
    use a manual brace-matcher rather than a regex."""
    out = OrderedDict()
    pat = re.compile(r"\\vertex\s*(?:\[([^\]]*)\])?\s*\(([^)]+)\)")
    for m in pat.finditer(src):
        pos = m.group(1)
        name = m.group(2).strip()
        # Skip whitespace after `)` and look for an optional `{...}` label
        j = m.end()
        while j < len(src) and src[j] in " \t":
            j += 1
        label = None
        if j < len(src) and src[j] == "{":
            end = _balanced_brace_match(src, j)
            if end > 0:
                label = src[j + 1:end - 1].strip()
                # Strip math delimiters; emit_tikz adds $...$ back.
                if label.startswith("$") and label.endswith("$"):
                    label = label[1:-1].strip()
                if label.startswith("\\(") and label.endswith("\\)"):
                    label = label[2:-2].strip()
        out[name] = Vertex(name=name, label=label, pos_spec=pos)
    return out


# ----- Diagram-body extraction --------------------------------------------

DIAGRAM_RE = re.compile(
    r"\\(?:feynmandiagram|diagram\*?)"
    r"\s*(?:\[[^\]]*\])?"            # optional [opts]
    r"\s*\{(.+?)\}\s*;",
    re.DOTALL,
)


def extract_diagram_body(src):
    m = DIAGRAM_RE.search(src)
    return m.group(1) if m else None


# ----- Diagram-body parsing -----------------------------------------------
#
# Body is a comma-separated list of chains; each chain is a sequence of
# (node, edge, node, edge, ..., node) tokens with `--` between.  A node is
# either `(name)` or `name [particle=...]`.  Edges are inside `[...]` after
# `--`.

def split_top_level(s, sep):
    """Split `s` on `sep` at brace/bracket nesting level zero."""
    depth = 0
    out = []
    cur = []
    for ch in s:
        if ch in "{[(":
            depth += 1
        elif ch in "}])":
            depth = max(0, depth - 1)
        if ch == sep and depth == 0:
            out.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if cur:
        out.append("".join(cur))
    return out


def parse_chain(chain, vertices, label_idx_by_chain):
    """Parse one chain like `i1 [particle=$e^-$] -- [fermion] a -- [photon] b`
    Returns list of edges; sets new vertices into `vertices` (in chain order).
    """
    edges = []

    # Split on `--` (preserve at depth 0 only)
    parts = []
    depth = 0
    cur = []
    i = 0
    while i < len(chain):
        c = chain[i]
        if c in "{[(":
            depth += 1; cur.append(c); i += 1; continue
        if c in "}])":
            depth = max(0, depth - 1); cur.append(c); i += 1; continue
        if depth == 0 and chain[i:i+2] == "--":
            parts.append("".join(cur).strip())
            cur = []
            i += 2
            continue
        cur.append(c)
        i += 1
    parts.append("".join(cur).strip())

    # Walk the parts, alternating between nodes and edge styles. The
    # invariant we want: edge_styles[i] is the style of the edge between
    # nodes[i] and nodes[i+1], so len(edge_styles) == len(nodes) - 1.
    nodes = []
    edge_styles = []
    expecting_edge = False    # True after a [opts] without a node-yet
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if p.startswith("["):
            m = re.match(r"\[([^\]]*)\]\s*(.*)", p, re.DOTALL)
            if not m:
                continue
            edge_styles.append(m.group(1))
            expecting_edge = False
            rest = m.group(2).strip()
            if rest:
                nodes.append(rest)
        else:
            # plain node. If we already have a node and the last gap had no
            # [opts], insert an empty edge style for that gap.
            if len(nodes) > 0 and len(edge_styles) < len(nodes):
                edge_styles.append("")
            nodes.append(p)

    # Sanity: trim trailing edge styles with no following node
    while len(edge_styles) >= len(nodes) and len(edge_styles) > 0:
        edge_styles.pop()

    # Process nodes — they may be `(name)` references or `name [particle=lbl]`
    # declarations. Convert each to a vertex name and add to vertices if new.
    node_names = []
    chain_x = label_idx_by_chain[0]    # initial x cursor for THIS chain
    chain_y = label_idx_by_chain[1]    # initial y cursor for THIS chain (y stays constant per chain)

    def _ensure_vertex(name, label=None):
        if name not in vertices:
            vertices[name] = Vertex(name=name, label=label)
        elif label and not vertices[name].label:
            vertices[name].label = label
        # If the vertex still has no position, place it on the chain cursor.
        v = vertices[name]
        if v.pos_spec is None and v.x is None:
            v.x = chain_x * 1.6
            v.y = chain_y * 1.4

    for n in nodes:
        n = n.strip()
        # Pattern: `(name)` or `(name.anchor)` (e.g. `(vertex.north)`)
        m = re.match(r"^\(([^)]+)\)$", n)
        if m:
            full = m.group(1).strip()
            base = full.split(".", 1)[0].strip()
            _ensure_vertex(base)
            # keep the full anchor-spec for the edge endpoint, so TikZ can
            # use \draw (a) -- (b.north) etc.
            node_names.append(full)
        else:
            # Pattern: `name [particle=lbl]` or just `name`
            m2 = re.match(r"^([A-Za-z0-9_]+)\s*(?:\[(.*)\])?$", n, re.DOTALL)
            if m2:
                name = m2.group(1).strip()
                attrs = m2.group(2) or ""
                label = _extract_particle_label(attrs)
                _ensure_vertex(name, label)
                node_names.append(name)
            else:
                # fallback: treat the whole token as a name
                name = re.sub(r"\W+", "_", n).strip("_") or f"v{len(vertices)}"
                _ensure_vertex(name)
                node_names.append(name)
        chain_x += 1

    # advance shared cursor across chains: x rewinds, y drops one row
    label_idx_by_chain[0] = 0
    label_idx_by_chain[1] = chain_y - 1

    # Build edges
    for i in range(len(node_names) - 1):
        edges.append((node_names[i], edge_styles[i] if i < len(edge_styles) else "", node_names[i+1]))

    return edges


# ----- Resolve positions --------------------------------------------------

def resolve_positions(vertices):
    """Compute (x, y) for each vertex based on its pos_spec. Vertices with
    no spec keep whatever auto-x/y they were given (e.g. by chain ordering),
    or default to (0, 0)."""
    placed = set()
    # First pass: any vertex with no spec but with x/y already set, mark placed
    for v in vertices.values():
        if v.pos_spec is None and (v.x is not None or v.y is not None):
            v.x = v.x or 0
            v.y = v.y or 0
            placed.add(v.name)

    # If no vertex placed yet, place the first one at (0, 0)
    if not placed:
        first = next(iter(vertices.values()))
        first.x = 0
        first.y = 0
        placed.add(first.name)

    # Iterate until stable
    changed = True
    while changed:
        changed = False
        for v in vertices.values():
            if v.name in placed:
                continue
            if v.pos_spec is None:
                v.x = v.x or 0
                v.y = v.y or 0
                placed.add(v.name)
                changed = True
                continue
            ps = parse_pos_spec(v.pos_spec)
            if ps is None:
                v.x = 0
                v.y = 0
                placed.add(v.name)
                changed = True
                continue
            anchor, dx, dy = ps
            if anchor in vertices and vertices[anchor].name in placed:
                v.x = vertices[anchor].x + dx
                v.y = vertices[anchor].y + dy
                placed.add(v.name)
                changed = True

    # Anyone still unplaced → (0, 0)
    for v in vertices.values():
        if v.x is None: v.x = 0
        if v.y is None: v.y = 0


# ----- Edge style → TikZ options ------------------------------------------

def _normalize_label(s):
    """Strip $ \( \) and outer braces from a label so it can be safely
    re-wrapped in $...$ on output."""
    s = s.strip()
    # Strip outer { }
    while s.startswith("{") and s.endswith("}"):
        s = s[1:-1].strip()
    # Strip outer $...$ or \(...\)
    if s.startswith("$") and s.endswith("$"):
        s = s[1:-1].strip()
    if s.startswith("\\(") and s.endswith("\\)"):
        s = s[2:-2].strip()
    return s


def style_to_tikz(style):
    """Map a tikz-feynman edge style description to plain TikZ draw options.
    Also returns a label spec extracted from the style."""
    s = style.strip()
    label = None
    label_below = False
    momentum = None

    m = re.search(r"edge\s*label\s*=\s*([^,\]]+)", s)
    if m:
        label = _normalize_label(m.group(1))
    m = re.search(r"edge\s*label'\s*=\s*([^,\]]+)", s)
    if m:
        label = _normalize_label(m.group(1))
        label_below = True
    m = re.search(r"momentum\s*=\s*([^,\]]+)", s)
    if m:
        momentum = _normalize_label(m.group(1))

    # Detect kind: order matters because "anti fermion" contains "fermion"
    s_low = s.lower()
    if "anti fermion" in s_low or "anti-fermion" in s_low:
        kind = "anti fermion"
    elif "charged scalar" in s_low:
        kind = "charged scalar"
    elif "fermion" in s_low:
        kind = "fermion"
    elif "photon" in s_low or "boson" in s_low:
        kind = "photon"
    elif "gluon" in s_low:
        kind = "gluon"
    elif "scalar" in s_low:
        kind = "scalar"
    elif "ghost" in s_low:
        kind = "ghost"
    else:
        kind = "plain"

    # TikZ draw opts per kind
    arrow_mid = ("postaction={decorate, decoration={markings, "
                 "mark=at position 0.55 with {\\arrow{Stealth}}}}")
    arrow_mid_rev = ("postaction={decorate, decoration={markings, "
                     "mark=at position 0.45 with {\\arrowreversed{Stealth}}}}")

    # NB: TikZJax preloads decorations.markings (so postaction-mark works) but
    # NOT decorations.pathmorphing (snake/coil). For boson/photon/gluon we
    # therefore avoid pathmorphing and use distinct stroke styles instead.
    if kind == "fermion":
        opts = arrow_mid
    elif kind == "anti fermion":
        opts = arrow_mid_rev
    elif kind == "charged scalar":
        opts = "dashed, " + arrow_mid
    elif kind == "scalar":
        opts = "dashed"
    elif kind == "photon":
        # solid line, dashed with very short dashes — visually distinct
        opts = "dash pattern=on 2pt off 2pt, line width=0.7pt"
    elif kind == "gluon":
        opts = "loosely dotted, line width=1.4pt, line cap=round"
    elif kind == "ghost":
        opts = "dotted"
    else:
        opts = ""

    return opts, label, label_below, momentum


# ----- Main entry point ---------------------------------------------------

def feynman_to_plain_tikz(block_src):
    """Take a string containing one tikz-feynman block (everything between
    \\begin{tikzpicture} ... \\end{tikzpicture}, OR a whole \\feynmandiagram
    {...}; expression) and return plain TikZ code that TikZJax can render.

    Returns None if parsing fails (caller falls back to a source listing)."""
    try:
        # We expect to be given the inside of \begin{tikzpicture}...\end{tikzpicture}
        # OR the whole \feynmandiagram[...]{...}; expression, both of which we
        # accept and trim down.

        # Trim outer tikzpicture if present
        m = re.search(r"\\begin\{tikzpicture\}(?:\[[^\]]*\])?(.*?)\\end\{tikzpicture\}",
                      block_src, re.DOTALL)
        inner = m.group(1) if m else block_src

        # Strip TeX %-comments — they ride along on lines that the chain
        # parser otherwise mistakes for vertex names.
        inner = re.sub(r"(?m)(?<!\\)%.*$", "", inner)

        # If inner doesn't actually contain feynman / feynmandiagram, no-op
        if "\\begin{feynman}" not in inner and "\\feynmandiagram" not in inner:
            return None

        # Parse explicit vertices first (Pattern A)
        vertices = parse_explicit_vertices(inner)

        # Then extract the diagram body and parse chains
        body = extract_diagram_body(inner)
        if body is None:
            return None

        chains = split_top_level(body, ",")
        all_edges = []
        cursor = [0, 0]    # (x cursor, y cursor)
        for c in chains:
            cs = c.strip()
            if not cs:
                continue
            edges = parse_chain(cs, vertices, cursor)
            all_edges.extend(edges)

        # If we had multiple chains and Pattern B (no explicit vertices),
        # stack them vertically so they don't pile up
        if len(chains) > 1 and not any(v.pos_spec for v in vertices.values()):
            # Recompute: spread chains by index
            # heuristic: assign y per chain by re-walking node_names
            # Easier: just accept overlaps for now; usually one chain anyway.
            pass

        resolve_positions(vertices)

        return emit_tikz(vertices, all_edges)
    except Exception as e:
        return None


def emit_tikz(vertices, edges):
    """Produce a \\usetikzlibrary{...} + \\begin{tikzpicture}...\\end{tikzpicture}
    string. TikZJax doesn't carry decorations.pathmorphing so we avoid snake/
    coil and only ask for decorations.markings + arrows.meta."""
    lines = []
    lines.append("\\usetikzlibrary{decorations.markings,arrows.meta}")
    lines.append("\\begin{tikzpicture}[every node/.style={font=\\small}]")
    # vertices — wrap label in $...$ since particle labels are bare TeX
    for v in vertices.values():
        label = v.label or ""
        if label:
            lines.append(f"  \\node ({v.name}) at ({v.x:.2f},{v.y:.2f}) {{${label}$}};")
        else:
            lines.append(f"  \\node ({v.name}) at ({v.x:.2f},{v.y:.2f}) {{}};")
    # edges
    for a, style, b in edges:
        opts, lab, below, mom = style_to_tikz(style)
        node_part = ""
        if lab:
            anchor = "below" if below else "above"
            node_part = f" node[{anchor}, midway, font=\\footnotesize] {{${lab}$}}"
        elif mom:
            node_part = f" node[above, midway, font=\\footnotesize] {{${mom}$}}"
        if opts:
            lines.append(f"  \\draw[{opts}] ({a}) --{node_part} ({b});")
        else:
            lines.append(f"  \\draw ({a}) --{node_part} ({b});")
    lines.append("\\end{tikzpicture}")
    return "\n".join(lines)
