#!/usr/bin/env python3
"""question_file.py - parse the subsystem question files.

A question file is markdown. It starts with a small header:

    # Questions: MM VMA Operations
    - guide: mm-vma.md
    - title: MM VMA Operations

then questions, each a heading, its fields and the question itself:

    ## vma.mmap-write-lock-effect: What taking the mmap write lock changes
    - section: What the mmap write lock does not exclude
    - relevance: 5 - why this matters when reviewing a patch

    The question, as plain prose, asking two or three things at most. No field
    says how long the answer is. (An old file's "- words: N" is read and
    ignored.) "- drafts: all" gives the builder every reader's draft for the
    whole guide, for the question that asks what models get wrong.

Any other top-level heading ("# Using VMAs safely") starts a part of the
guide; the sections after it render beneath it. Consecutive questions that
name the same section render under one heading, each as a short bulleted list
under its own title, and are put to the model together. Quick checks that belong together say so with "- group: <label>";
the label is not rendered. A top-level "# Quick checks"
heading makes the questions after it render as bullets under "Quick Checks";
"# Sections" switches back.

An item may be text to insert instead of a question to answer:

    ## gicv3.its-command-rules: What the architecture says about ITS commands
    - section: The ITS command queue
    - verbatim: ../verbatim/gic-v3-its-commands.md

The file, named relative to the question file, is put into the guide under
that title exactly as it is, every build, and no model sees it. It is for what
a kernel tree cannot answer: a specification's wording, a method.

The header may also say "- min-relevance: 3": build this guide from the
questions at that relevance and up, unless the command line says otherwise.

A whole guide can be hand-maintained the same way. A question file whose
header has "- verbatim: ../verbatim/races.md" and no questions builds to a copy
of that file, so that a build directory holds every guide a review can load.

The built guides are in kernel/subsystem/build/linus/ (BUILD_DIR): the guides
built from the most recent tree of Linus's that was scanned. The file
kernel-version.yaml in that directory records the release and the commit.

Shared by lint-questions.py and build-guides.py. See
kernel/docs/subsystem-questions.md.
"""

import os

import re

HEADING_RE = re.compile(r"^## (\S+): (.+)$")
# An id becomes a file name (answers/<id>.md), so it may be nothing but a name.
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*(\.[A-Za-z0-9][A-Za-z0-9_-]*)*$")


def safe_id(qid):
    """True if an id can be used as a file name: no separators, no dot-dot."""
    return bool(ID_RE.match(qid)) and os.path.basename(qid) == qid
FIELD_RE = re.compile(r"^- ([a-z\-]+): (.+)$")
RELEVANCE_RE = re.compile(r"^([0-5]) - \S.+")
SHA_RE = re.compile(r"\b[0-9a-f]{12,40}\b")
HISTORY_RE = re.compile(r"\b(since|before|until|after|as of) v\d|\bin v\d+\.\d+"
                        r"|\b(earlier|older|previous|prior) (kernels|releases|versions)\b", re.I)
HEADER = ("guide", "title")
HEADER_OPTIONAL = ("verbatim", "min-relevance")
FIELDS = ("section", "group", "relevance", "words", "verbatim", "drafts")
OLD_FORMAT_RE = re.compile(r"^### (Concern|Ask|Hypotheses|Falsify|Seeds)\s*$", re.M)


VERBATIM_MAX_BYTES = 200 * 1024

SUBSYSTEM_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             "subsystem")
QUESTIONS_DIR = os.path.join(SUBSYSTEM_DIR, "questions")
# The directory is named for whose tree is scanned, not for a release: it is
# rebuilt whenever that tree has moved on, and a name with the release in it
# would change with every rebuild.
BUILD_DIR = os.path.join(SUBSYSTEM_DIR, "build", "linus")


def resolve_verbatim(question_path, value):
    """Where a '- verbatim:' value points, and what is wrong with it if anything.

    A question file can arrive in a patch, and the file it names is copied into
    a guide, so the name is confined: relative, a markdown file, no symbolic
    link anywhere in it, and inside the directory above the question file
    (kernel/subsystem/ for a build set). Returns (path, None) or (None, why).
    """
    if os.path.isabs(value) or value.startswith("~"):
        return None, "verbatim path must be relative to the question file"
    if not value.endswith(".md"):
        return None, "verbatim file must be a .md file"
    base = os.path.dirname(os.path.abspath(question_path))
    root = os.path.dirname(base)
    path = os.path.normpath(os.path.join(base, value))
    if os.path.commonpath([root, path]) != root:
        return None, f"verbatim file must be under {os.path.relpath(root)}"
    if os.path.realpath(path) != os.path.join(os.path.realpath(root),
                                              os.path.relpath(path, root)):
        return None, "verbatim path goes through a symbolic link"
    return path, None


def read_verbatim(path):
    with open(path, "rb") as f:
        data = f.read(VERBATIM_MAX_BYTES + 1)
    if len(data) > VERBATIM_MAX_BYTES:
        raise OSError(f"{path} is larger than {VERBATIM_MAX_BYTES} bytes")
    return data.decode("utf-8").strip()


class Question:
    def __init__(self, path, line, qid, title, quick, part=None):
        self.path, self.line, self.id, self.title = path, line, qid, title
        self.quick = quick          # renders as a bullet under Quick Checks
        self.part = part            # the part of the guide it belongs to, if any
        self.fields = {}
        self.text = ""

    @property
    def relevance(self):
        m = RELEVANCE_RE.match(self.fields.get("relevance", ""))
        return int(m.group(1)) if m else None

    @property
    def section(self):
        return self.fields.get("section")

    @property
    def group(self):
        """Questions with the same group are put to the model together."""
        return self.fields.get("group") or self.section

    @property
    def verbatim(self):
        """Path of the text this item inserts as it is, or None for a question."""
        v = self.fields.get("verbatim")
        return resolve_verbatim(self.path, v)[0] if v else None

    @property
    def verbatim_problem(self):
        v = self.fields.get("verbatim")
        return resolve_verbatim(self.path, v)[1] if v else None

    def verbatim_text(self):
        if not self.verbatim:
            raise OSError(self.verbatim_problem or "not a verbatim item")
        return read_verbatim(self.verbatim)

    @property
    def is_verbatim(self):
        """True for an item that names a file, whether or not the name is allowed."""
        return "verbatim" in self.fields

    @property
    def words(self):
        if self.is_verbatim:
            try:
                return len(self.verbatim_text().split())
            except OSError:
                return None
        w = self.fields.get("words", "")
        return int(w) if w.isdigit() else None


def parse(path):
    """Return (header dict, [Question], [(line, id, message)])."""
    header, questions, problems = {}, [], []
    cur, quick, in_fields, part, seen_top = None, False, False, None, False
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    for n, line in enumerate(lines, 1):
        if line.startswith("## "):
            m = HEADING_RE.match(line)
            if not m:
                problems.append((n, "-", f"heading is not '## <id>: <title>': {line}"))
                cur = None
                continue
            if not safe_id(m.group(1)):
                problems.append((n, "-", "an id is letters, digits, '-', '_' and single "
                                 f"dots between them, since it names a file: {m.group(1)}"))
                cur = None
                continue
            cur = Question(path, n, m.group(1), m.group(2).strip(), quick, part)
            questions.append(cur)
            in_fields = True
            continue
        if line.startswith("# "):
            cur = None
            name = line[2:].strip().lower()
            if name.startswith("quick check"):
                quick, part = True, None
            elif name.startswith("section"):
                quick, part = False, None
            elif seen_top:                  # the first one is the file's own title
                quick, part = False, line[2:].strip()
            seen_top = True
            continue
        m = FIELD_RE.match(line)
        if cur is None:
            if m and not questions and m.group(1) in HEADER + HEADER_OPTIONAL:
                header[m.group(1)] = m.group(2).strip()
            continue
        if in_fields and m:
            cur.fields[m.group(1)] = m.group(2).strip()
            continue
        if in_fields and not line.strip() and not cur.fields:
            continue
        in_fields = False
        cur.text += line + "\n"
    for q in questions:
        q.text = q.text.strip()
    if header.get("verbatim"):
        where, why = resolve_verbatim(path, header["verbatim"])
        if why:
            problems.append((1, "-", why))
        header["verbatim"] = where
    return header, questions, problems
