#!/usr/bin/env python3
"""check-built-guide.py - check a built subsystem guide before it is committed.

For each guide named (default: every guide in the build directory,
kernel/subsystem/build/linus/) it checks:

- the build set lints clean;
- every question the build set selects has a kept answer, none empty, and
  rendering from the kept answers reproduces the guide exactly, so the guide
  was not edited by hand and can be rendered again without a model;
- the kernel the build was made from is recorded in kernel-version.yaml;
- nothing in the guide, its answers or its question files names a model or
  looks like a run's cost or a path on the machine that built it: a home
  directory, or the scratch directory a build worked in. A path under /tmp that
  the kernel's own code or tests use is a fact about the kernel and is left
  alone. Model names are always checked, two ways. Patterns built in here catch the vendor and product names, a family
  name with a version after it, and the shape of a model identifier. And the
  models that were actually used are read from two local files, so whatever
  built the guide is refused by name without this public repository listing
  it: ~/.config/review-prompts/models-seen, to which build-guides.py adds every
  model it is ever told to use on this machine, however the build was started,
  and ~/.config/review-prompts/build.env (or the file $REVIEW_PROMPTS_CONFIG
  names), which names them for rebuild-guides.sh. $REVIEW_PROMPTS_FORBIDDEN
  adds a regular expression of your own.

The build directory holds the guides of one kernel: the most recent tree of
Linus's that was scanned. To move to a newer kernel, build every guide again.

Usage:
    check-built-guide.py [--dir kernel/subsystem/build/linus] [guide ...]

See kernel/docs/subsystem-questions.md.
"""

import argparse
import glob
import importlib.util
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KERNEL_DIR = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from question_file import BUILD_DIR, QUESTIONS_DIR, parse  # noqa: E402

_spec = importlib.util.spec_from_file_location("build_guides",
                                              os.path.join(HERE, "build-guides.py"))
assert _spec and _spec.loader, "build-guides.py must sit beside this script"
bg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bg)

# A cost, a home directory, or a temporary directory that a build made or that
# holds a copy of the tree. Not every path under /tmp: the kernel's tests name
# some, and a guide may say so.
NOT_PUBLIC = (r"\$[0-9]+\.[0-9]{2}\b|/root/|/home/[a-z]|"
              r"(?:/var)?/tmp/[^\s`'\"<>]*(?:build-guides|rebuild-guides|snapshot/linux|claude)")
# Always on. Nothing here can be kernel text: "gpt" and "gemini" are left out
# because a partition table and an SoC are called that.
MODEL_NAMES = "|".join((
    r"\bclaude\b", r"\banthropic\b", r"\bopenai\b",
    r"\b(opus|sonnet|haiku)[ -]?v?\d",                  # a family name and a version
    r"\b[a-z][a-z0-9]*(-[a-z0-9]+)*-v?\d+(-\d+)*-(fast|prod|preview|latest)\b",   # xxx-v1-1-fast
    r"\b[a-z][a-z0-9]*(-[a-z0-9]+)+-20\d{6}\b",         # xxx-yyy-20250101
))
MODEL_VARS = ("REVIEW_PROMPTS_BUILDER", "REVIEW_PROMPTS_READERS", "REVIEW_PROMPTS_CHECKER")


def local_models():
    """The model ids this machine builds with, and where they were found.

    From the environment and from the file rebuild-guides.sh reads. The names
    are never printed: a report of this check may end up in public too.
    """
    path = os.environ.get("REVIEW_PROMPTS_CONFIG") or os.path.expanduser(
        "~/.config/review-prompts/build.env")
    values = [os.environ.get(v, "") for v in MODEL_VARS]
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"\s*(?:export\s+)?(\w+)=(.*)$", line)
                if m and m.group(1) in MODEL_VARS:
                    values.append(m.group(2).split("#")[0].strip().strip("'\""))
        found = path
    except OSError:
        found = None
    seen = os.path.expanduser(os.environ.get("REVIEW_PROMPTS_MODELS_SEEN")
                              or "~/.config/review-prompts/models-seen")
    try:
        with open(seen, encoding="utf-8") as f:
            values += [line.strip() for line in f]
        found = found or seen
    except OSError:
        pass
    ids = {w for v in values for w in v.split() if w}
    return ids, found


def forbidden_pattern():
    """One regular expression for everything that must not be committed."""
    ids, found = local_models()
    parts = [NOT_PUBLIC, MODEL_NAMES]
    for mid in sorted(ids):
        parts.append(re.escape(mid))
        lead = re.match(r"[A-Za-z]{4,}", mid)       # an id's first word names the family
        if lead:
            parts.append(r"\b" + re.escape(lead.group(0)) + r"\b")
    scratch = os.environ.get("REVIEW_PROMPTS_SCRATCH", "")
    if scratch:                                     # wherever this build worked
        parts.append(re.escape(os.path.abspath(scratch)))
    extra = os.environ.get("REVIEW_PROMPTS_FORBIDDEN", "")
    if extra:
        parts.append(extra)
    note = ("model names: built-in patterns and the "
            f"{len(ids)} model(s) this machine has built with" if ids else
            "model names: built-in patterns only; no local list of the models used was "
            f"found ({'in ' + found if found else 'no build.env'})")
    return re.compile("|".join(f"(?:{p})" for p in parts), re.I), note



def recorded(build_dir):
    """{"kernel": ..., "sha": ...} from kernel-version.yaml; {} if it records none."""
    return bg.read_record(os.path.join(build_dir, "kernel-version.yaml"))


def record_problem(build_dir):
    """What is wrong with the kernel record of a build directory, or None."""
    if not recorded(build_dir):
        return "kernel-version.yaml does not record the kernel"
    return None


def check(guide, build_dir, forbidden):
    problems, notes = [], []
    qfile = os.path.join(QUESTIONS_DIR, guide + ".md")
    built = os.path.join(build_dir, guide + ".md")
    if not os.path.isfile(qfile):
        return [f"no question file {os.path.relpath(qfile)}"], notes
    if not os.path.isfile(built):
        return [f"no built guide {os.path.relpath(built)}"], notes
    lint = subprocess.run([os.path.join(HERE, "lint-questions.py"), qfile],
                          capture_output=True, text=True)
    if lint.returncode:
        problems.append("the build set does not lint: " + lint.stdout.strip().split("\n")[0])
    header, questions, _ = parse(qfile)
    with open(built, encoding="utf-8") as f:
        text = f.read()
    if header.get("verbatim"):
        with open(header["verbatim"], encoding="utf-8") as f:
            if f.read().rstrip() + "\n" != text:
                problems.append("differs from the hand-maintained file it is a copy of")
        notes.append(f"copied whole from {os.path.relpath(header['verbatim'])}")
    else:
        asked = bg.select({guide: (header, questions)}, None, set())[guide]
        kept = os.path.join(build_dir, "answers", guide)
        answers = {}
        for q in questions:
            if q.is_verbatim:
                answers[q.id] = q.verbatim_text()
                continue
            path = bg.answer_path(kept, q.id)
            if os.path.isfile(path) and not os.path.islink(path):
                with open(path, encoding="utf-8") as f:
                    answers[q.id] = f.read().strip()
        # How long a guide is is reported and nothing more: no number decides it.
        # The builder writes what a reviewer needs and the read-through distils.
        total = sum(len(answers[q.id].split()) for q in asked
                    if not q.is_verbatim and answers.get(q.id))
        notes.append(f"{total} words of answers; the guide is {len(text.split())} with "
                     "titles, headings and inserted text")
        gone = [q.id for q in asked if not answers.get(q.id)]
        if gone:
            problems.append("no kept answer for: " + ", ".join(gone[:6]))
        elif bg.render(header, guide, [q for q in questions if q.id in answers],
                       answers, False) != text:
            problems.append("rendering the kept answers does not give this guide: it was "
                            "edited by hand, or the answers are from another build")
        else:
            notes.append(f"{sum(1 for q in asked if not q.is_verbatim)} answers kept; "
                         "rendering them reproduces the guide")
    if record_problem(build_dir):
        problems.append(record_problem(build_dir))
    scan = [built, qfile] + glob.glob(os.path.join(build_dir, "answers", guide, "*.md"))
    scan += glob.glob(os.path.join(QUESTIONS_DIR, "catalogue", guide + "-measurement*.md"))
    pattern, note = forbidden
    notes.append(note)
    for path in scan:
        with open(path, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                if pattern.search(line):
                    # say where, not what: this output gets pasted into commits
                    problems.append(f"{os.path.relpath(path)}:{n}: names a model, a cost "
                                    "or a local path")
                    break
    return problems, notes


def main():
    ap = argparse.ArgumentParser(description="Check built subsystem guides.")
    ap.add_argument("guides", nargs="*")
    ap.add_argument("--dir", default=BUILD_DIR,
                    help="the build directory the guides are in (default: "
                    "kernel/subsystem/build/linus)")
    opts = ap.parse_args()
    build_dir = os.path.abspath(opts.dir)
    # a guide is a file in the build directory that has a question file
    guides = opts.guides or sorted(
        os.path.basename(p)[:-3] for p in glob.glob(os.path.join(build_dir, "*.md"))
        if os.path.isfile(os.path.join(QUESTIONS_DIR, os.path.basename(p))))
    forbidden = forbidden_pattern()
    failed = 0
    for g in guides:
        problems, notes = check(g, build_dir, forbidden)
        print(f"{g}: " + ("PROBLEMS" if problems else "ok"))
        for line in notes:
            print("  " + line)
        for line in problems:
            print("  PROBLEM: " + line)
        failed += bool(problems)
    if len(guides) > 1:
        print(f"{len(guides) - failed} of {len(guides)} ok")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
