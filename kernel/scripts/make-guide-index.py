#!/usr/bin/env python3
"""make-guide-index.py - write the index of the subsystem guides.

A review searches the index for the files and names a patch touches, and reads
the answers that the search finds. The index has one line for each answer of
every guide in the build directory, kernel/subsystem/build/linus/:

    ## <section> ### <title>, <guide>:<line>, <source file>, <symbols>

    section, title   the headings the answer is under in its guide
    guide, line      the guide file, and the line where the answer starts
    source file      the one file of the kernel tree that the answer is mostly
                     about: the .c file that defines the most of the functions,
                     macros and structures the answer names, or a header if no
                     .c file defines any. Left out if no file defines any
    symbols          every function, macro, structure, field and option the
                     answer names in backticks, in the order it names them.
                     Keywords of C, true, false, NULL and the base types
                     (int, unsigned long, u64, size_t and the like) are left
                     out: a search for one of them finds every guide

It needs no model. It needs the kernel tree the guides were built from, to
find where each name is defined. Run it again whenever a guide changes: the
line numbers in the index are those of the guides it was made from.

Usage:
    make-guide-index.py --tree <linux> [--dir kernel/subsystem/build/linus] [--out FILE]
    make-guide-index.py --tree <linux> --check
"""

import argparse
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field

from question_file import BUILD_DIR, QUESTIONS_DIR

INDEX = "subsystem-guide-index.txt"
# files that are not guides, in case --dir names a directory that holds some
NOT_GUIDES = {"subsystem.md", "README.md", "subjective-review.md"}

TICK_RE = re.compile(r"`([^`\n]+)`")
SYMBOL_RE = re.compile(r"^(?:(?:struct|union|enum) )?[A-Za-z_][A-Za-z0-9_]*"
                       r"(?:(?:->|\.|::)[A-Za-z_][A-Za-z0-9_]*)*(?:\(\))?$")
PATH_RE = re.compile(r"^(?:[\w.+-]+/)+[\w.+-]+$")
SECTION_RE = re.compile(r"^## (.+)$")
# The build writes a title in three forms: alone on a line, in front of the
# sentence an answer opens with, and in front of a one-line answer in a list.
TITLE_RE = re.compile(r"^### (.+)$|^\*\*([^*\n]+)\*\*$")
LEAD_TITLE_RE = re.compile(r"^\*\*([^*\n]+):\*\* |^- \*\*([^*\n]+)\*\*: ")
QUESTION_RE = re.compile(r"^## [\w.-]+: (.+)$", re.M)
# a definition in kernel style starts in the first column
FUNCTION_RE = re.compile(r"^(?!#)(?:[A-Za-z_][\w\s\*]*?[\s\*])?([A-Za-z_]\w*)\s*\([^;]*$")
MACRO_RE = re.compile(r"^#\s*define\s+([A-Za-z_]\w*)\b")
TYPE_RE = re.compile(r"^(?:struct|union|enum)\s+([A-Za-z_]\w*)\s*\{")
NOT_NAMES = {"if", "while", "for", "switch", "return", "sizeof", "defined"}
# What a guide writes in backticks and a search must not find: the words of the
# language, and the base types. A patch has them on nearly every line.
NOT_SYMBOLS = frozenset("""
    auto break case char const continue default do double else enum extern float
    for goto if inline int long register restrict return short signed sizeof
    static struct switch typedef union unsigned void volatile while
    _Atomic _Bool _Generic _Static_assert asm typeof typeof_unqual
    __asm__ __inline__ __volatile__ __typeof__
    bool true false NULL
    size_t ssize_t ptrdiff_t uintptr_t intptr_t uint ulong ushort uchar
    u_char u_short u_int u_long usize isize f32 f64
""".split())
# u8 to u128 and s8 to s128, with or without "__"; __le16 to __be64; uint8_t to
# int64_t; i8 to i128 in Rust
BASE_TYPE_RE = re.compile(r"^(?:(?:__)?[us]|i)(?:8|16|32|64|128)$"
                          r"|^(?:__)?(?:le|be)(?:16|32|64)$"
                          r"|^u?int(?:8|16|32|64)_t$")
# a name defined in more files than this says nothing about which file an answer is about
TOO_MANY_FILES = 4
# copies of kernel names made for tests and examples; the kernel's own file is the one to list
COPIES = ("tools/", "samples/")


@dataclass
class Answer:
    guide: str
    section: str
    title: str
    line: int
    body: list[str] = field(default_factory=list)


def tree_files(tree: str) -> list[str]:
    """The files of the tree: what git tracks, or what is on disk if it is a plain copy."""
    r = subprocess.run(["git", "-C", tree, "ls-files"], capture_output=True, text=True, check=False)
    if r.returncode == 0 and r.stdout:
        return r.stdout.split("\n")
    out = []
    for root, dirs, names in os.walk(tree):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        out += [os.path.relpath(os.path.join(root, n), tree) for n in names]
    return out


def definitions(tree: str, files: list[str]) -> dict[str, set[str]]:
    """{name: the files that define it}, for functions, macros and types."""
    defs: dict[str, set[str]] = defaultdict(set)
    for f in files:
        if not f.endswith((".c", ".h")):
            continue
        try:
            with open(os.path.join(tree, f), encoding="utf-8", errors="replace") as src:
                for line in src:
                    if line[:1] in " \t\n/*}":
                        continue
                    m = MACRO_RE.match(line) or TYPE_RE.match(line) or FUNCTION_RE.match(line)
                    if m and m.group(1) not in NOT_NAMES:
                        defs[m.group(1)].add(f)
        except OSError:
            continue
    return defs


def question_titles(path: str) -> set[str]:
    """The titles of the questions a guide was built from; none if it has no question file."""
    name = os.path.join(QUESTIONS_DIR, os.path.basename(path))
    try:
        with open(name, encoding="utf-8") as f:
            return {t.strip() for t in QUESTION_RE.findall(f.read())}
    except OSError:
        return set()


def answers(path: str) -> Iterator[Answer]:
    """The answers of one guide, each with the line its title is on."""
    guide = os.path.basename(path)
    known = question_titles(path)
    section, cur = "", None
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.rstrip("\n")
            sec, title = SECTION_RE.match(line), TITLE_RE.match(line)
            lead = LEAD_TITLE_RE.match(line)
            # "**Unsafe usage**:" has the same form as a title in front of text, so
            # that form counts only for a title that a question has
            if lead and (lead.group(1) or lead.group(2)).strip() in known:
                if cur:
                    yield cur
                cur = Answer(guide, section, (lead.group(1) or lead.group(2)).strip(), n,
                             [line[lead.end():]])
                continue
            if sec:
                if cur:
                    yield cur
                section, cur = sec.group(1).strip(), None
            # a bold line alone is a title if a question has that title; inside text
            # that a build copies, such as races.md, it is part of the text
            elif title and (title.group(1) or title.group(2).strip() in known):
                if cur:
                    yield cur
                cur = Answer(guide, section, (title.group(1) or title.group(2)).strip(), n)
            elif cur:
                cur.body.append(line)
    if cur:
        yield cur


def symbols(a: Answer) -> list[str]:
    out: list[str] = []
    for t in TICK_RE.findall("\n".join(a.body)):
        t = t.strip()
        name = t.removesuffix("()")
        if (len(t) > 2 and SYMBOL_RE.match(t) and t not in out
                and name not in NOT_SYMBOLS and not BASE_TYPE_RE.match(name)):
            out.append(t)
    return out


def source_file(a: Answer, names: list[str], defs: dict[str, set[str]], known: set[str]) -> list[str]:
    """The file the answer is mostly about, as a list of one, or of none."""
    count: Counter[str] = Counter()
    for s in names:
        name = re.sub(r"^(?:struct|union|enum) ", "", s).removesuffix("()")
        found = defs.get(name, set())
        found = {f for f in found if not f.startswith(COPIES)} or found
        found = {f for f in found if f.endswith(".c")} or found
        if 0 < len(found) <= TOO_MANY_FILES:
            count.update(found)
    for t in TICK_RE.findall("\n".join(a.body)):
        t = t.strip()
        if PATH_RE.match(t) and t in known:
            count[t] += 1
    return sorted(count, key=lambda f: (not f.endswith(".c"), -count[f], f))[:1]


def index(tree: str, directory: str) -> list[str]:
    files = tree_files(tree)
    known, defs = set(files), definitions(tree, files)
    if not defs:
        raise SystemExit(f"{tree}: no .c or .h file with a definition; is it a kernel tree?")
    lines = []
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".md") or name in NOT_GUIDES:
            continue
        for a in answers(os.path.join(directory, name)):
            names = symbols(a)
            lines.append(", ".join([f"## {a.section} ### {a.title}", f"{a.guide}:{a.line}",
                                    *source_file(a, names, defs, known),
                                    *(f"`{s}`" for s in names)]))
    return lines


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n", 1)[0])
    ap.add_argument("--tree", required=True, help="the kernel tree the guides were built from")
    ap.add_argument("--dir", default=BUILD_DIR,
                    help="the build directory the guides are in (default: "
                    "kernel/subsystem/build/linus)")
    ap.add_argument("--out", help=f"the index to write (default: {INDEX} beside the guides)")
    ap.add_argument("--check", action="store_true",
                    help="write nothing; fail if the index is not the one these guides and "
                    "this tree give")
    opts = ap.parse_args()
    out = opts.out or os.path.join(opts.dir, INDEX)
    text = "\n".join(index(opts.tree, opts.dir)) + "\n"
    if opts.check:
        try:
            with open(out, encoding="utf-8") as f:
                same = f.read() == text
        except OSError:
            same = False
        print(f"{out}: {'ok' if same else 'not current: make it again'}")
        return 0 if same else 1
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"{out}: {text.count(chr(10))} answers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
