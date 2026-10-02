#!/usr/bin/env python3
"""lint-questions.py - check the subsystem question files.

Checks that each file under kernel/subsystem/questions/ follows the format in
kernel/docs/subsystem-questions.md: the header, a '## <id>: <title>' heading
per question, a relevance score with its reason, a question, no repeated ids,
and no commit SHAs or "since vX.Y" history. --table lists each file's
questions by relevance. A question says nothing about how long its answer is.

Diagnostics are one line each, <file>:<line>: <id>: <message>, and any of them
makes the exit status non-zero.

Usage:
    lint-questions.py [--table] kernel/subsystem/questions/*.md
"""

import argparse
import os
import re
import sys
from collections import Counter

from question_file import (FIELDS, HEADER, HISTORY_RE, OLD_FORMAT_RE, RELEVANCE_RE,
                           SHA_RE, parse)


TITLE_CLAUSE_RE = re.compile(r"^(What|Which|How|When|Where|Why|Who|Is|Are|Does|Do|Can)\b")


def check_verbatim(q):
    for name in q.fields:
        if name not in ("section", "verbatim"):
            yield f"a verbatim item takes only section and verbatim, not '{name}'"
    if q.text:
        yield "a verbatim item has no question; the text comes from the file it names"
    if q.verbatim_problem:
        yield q.verbatim_problem
    elif not os.path.isfile(q.verbatim):
        yield f"verbatim file not found: {os.path.relpath(q.verbatim)}"
    elif not q.words:
        yield f"verbatim file is empty or too large: {os.path.relpath(q.verbatim)}"


def check(q):
    if q.is_verbatim:
        if len(q.title.split()) > 8:
            yield f"the title is {len(q.title.split())} words; a heading is short"
        yield from check_verbatim(q)
        return
    if TITLE_CLAUSE_RE.match(q.title):
        yield ("the title restates the question; make it the topic a reviewer would "
               "scan for, as a short noun phrase")
    elif len(q.title.split()) > 6:
        yield f"the title is {len(q.title.split())} words; a heading is two to five"
    if q.title.endswith((".", "?", ":")):
        yield "the title ends in punctuation; it is rendered as a heading"
    above = {re.sub(r"\W+", " ", h or "").strip().lower() for h in (q.part, q.section)}
    if re.sub(r"\W+", " ", q.title).strip().lower() in above - {""}:
        yield ("the title repeats the heading above it; name the thing this answer is "
               "about within that subject")
    for name in q.fields:
        if name not in FIELDS:
            yield (f"unknown field '{name}'; a question has section or group, and "
                   "relevance")
    if q.fields.get("drafts") not in (None, "all"):
        yield "drafts is 'all' or absent: whether the builder sees every reader's draft for the guide"
    if not RELEVANCE_RE.match(q.fields.get("relevance", "")):
        yield "relevance must be '<0-5> - <one-line reason>'"
    if q.quick and q.section:
        yield "a quick check does not take a section; use group to say what it goes with"
    if q.section and q.fields.get("group"):
        yield "a section's questions are already a group; drop the group field"
    if q.text.count("?") > 3:
        yield (f"{q.text.count('?')} question marks: one question asks one thing; "
               "split it")
    if len(q.text.split()) < 8:
        yield "no question"
    if OLD_FORMAT_RE.search(q.text):
        yield "old format (### Concern/Ask/...); write the question as plain prose"
    if SHA_RE.search(q.text):
        yield "looks like a commit or blob SHA; name a commit by its subject"
    if HISTORY_RE.search(q.text):
        yield ("asks about history ('since vX.Y', 'earlier kernels'); a build from one "
               "tree cannot answer that and will invent it; ask about this tree")


def main():
    ap = argparse.ArgumentParser(description="Check the subsystem question files.")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--table", action="store_true",
                    help="list each file's questions by relevance")
    opts = ap.parse_args()
    failed, seen = False, {}
    for path in opts.files:
        name = os.path.relpath(path)
        with open(path, encoding="utf-8") as f:
            if OLD_FORMAT_RE.search(f.read()):
                print(f"{name}:1: -: still in the old format (### Concern/Ask/...); "
                      "rewrite each question as plain prose with a relevance")
                failed = True
                continue
        header, questions, problems = parse(path)
        out = list(problems)
        for key in HEADER:
            if key not in header:
                out.append((1, "-", f"header has no '- {key}:' line"))
        if "min-relevance" in header and header["min-relevance"] not in list("012345"):
            out.append((1, "-", "min-relevance in the header must be a number from 0 to 5"))
        if header.get("verbatim"):
            if not os.path.isfile(header["verbatim"]):   # a refused name is already a problem
                out.append((1, "-", "verbatim file not found: "
                            + os.path.relpath(header["verbatim"])))
            if questions:
                out.append((1, "-", "a guide that is copied whole from a verbatim file "
                            "has no questions of its own"))
        for q in questions:
            if q.id in seen:
                out.append((q.line, q.id, f"id already used at {seen[q.id]}"))
            seen.setdefault(q.id, f"{name}:{q.line}")
            out += [(q.line, q.id, m) for m in check(q)]
        for n, qid, msg in sorted(out):
            print(f"{name}:{n}: {qid}: {msg}")
        failed |= bool(out)
        hist = Counter(q.relevance for q in questions if q.relevance is not None)
        spread = " ".join(f"{k}:{hist[k]}" for k in sorted(hist, reverse=True))
        pasted = [q for q in questions if q.is_verbatim]
        print(f"{name}: {len(questions) - len(pasted)} questions, "
              f"relevance {spread}"
              + (f"; {len(pasted)} verbatim items, {sum(q.words or 0 for q in pasted)} words"
                 if pasted else ""), file=sys.stderr)
        if opts.table:
            for q in sorted(questions, key=lambda q: (-(q.relevance or -1), q.id)):
                kind = "verbatim" if q.is_verbatim else "check  " if q.quick else "section"
                print(f"  {q.relevance}  {kind}  {q.id:34s} {q.title}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
