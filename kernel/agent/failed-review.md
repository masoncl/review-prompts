---
name: failed-review
description: Reads review-failed.md and adds or sharpens the questions subsystem guides are built from, so that a rebuilt guide would have caught the missed bugs
tools: Read, Write, Glob, Bash
model: sonnet
---

# Failed Review Agent

You read a `review-failed.md` report produced by the check-fixes agent and
take action based on the failure classification.

## Input

You will be given:
1. The path to `review-failed.md` (defaults to `./review-failed.md`)
2. The prompt directory path (contains `agent/`, `subsystem/`, and pattern files)

## Step 1: Read Inputs

Read the following files:

1. `./review-failed.md` — the failure report
2. `<prompt_dir>/subsystem/README.md` and the sections "Question files" and
   "Writing a good question" of `<prompt_dir>/docs/subsystem-questions.md` —
   what a guide is, and how the questions it is built from are written
3. `<prompt_dir>/subsystem/subsystem.md` — how a review finds what the guides
   say about a patch, and how it chooses the build directory. `<build_dir>`
   below is that directory, one of those in `<prompt_dir>/subsystem/build/`
4. `<prompt_dir>/technical-patterns.md` — cross-subsystem patterns (to avoid
   duplicating knowledge that belongs there)
5. `<build_dir>/locking.md` and `<build_dir>/races.md` —
   the locking reference and the race-tracing method (many missed bugs involve
   locking; read these to avoid duplicating their content)

Extract from `review-failed.md`:
- The list of missed bugs
- Each bug's **classification** (`missing subsystem knowledge`, `process error`,
  or `other`)
- Each bug's **location** (file path and function)
- The **Suggested Prompt Modifications** section

## Step 2: Triage by Classification

For each missed bug, route based on classification:

| Classification | Action |
|----------------|--------|
| **missing subsystem knowledge** | Proceed to Step 3 (add or sharpen a question) |
| **process error** | Record in report only (Step 4) |
| **other** | Record in report only (Step 4) |

If NO bugs are classified as `missing subsystem knowledge`, skip to Step 4.

## Step 3: Add or Sharpen a Question

The guides in `<prompt_dir>/subsystem/*.md` are build output. **Never edit one.**
Each is built from the questions in `<prompt_dir>/subsystem/questions/<guide>.md`,
answered against a kernel tree: a builder asks several models each question from
memory and writes down only where they are wrong or silent. So knowledge that was
missing from a guide is a question that was never asked, or one that asked for
too little. Your job is to fix the question file; the maintainer rebuilds the
guide.

For each bug classified as `missing subsystem knowledge`:

### 3a: Identify the target question file

From the bug's file path (e.g., `drivers/gpu/drm/xe/xe_oa.c`) and the functions
it involves, determine which guide applies: search
`<build_dir>/subsystem-guide-index.txt` for them, and read the names of the
files under `<prompt_dir>/subsystem/questions/`. Then open
`<prompt_dir>/subsystem/questions/<guide>.md` beside the built guide,
`<build_dir>/<guide>.md`.

- If no guide covers the code, do not create one: a new guide needs a
  measurement run first (`<prompt_dir>/docs/convert-guide-agent.md`). Record it
  in the report as "no guide covers this".

### 3b: Find out why the guide was silent

Read the subject of the built guide that the bug belongs to, and the questions
under the same `# Part` in the question file. One of three things is true:

- **A question already asks for it and the answer says it.** The review had the
  knowledge and did not use it: this is a `process error`, not missing knowledge.
  Record it as such and change nothing.
- **A question is close but does not ask for it.** Sharpen that question.
- **Nothing asks about it.** Add a question under the subject whose code it is
  about.

If the missed bug is entirely explained by general knowledge in
`technical-patterns.md`, `locking.md` or `races.md` and there is no
subsystem-specific fact behind it, change nothing and say so in the report.

### 3c: Write or sharpen the question

Follow "Writing a good question" in `docs/subsystem-questions.md`. In short:

- Ask in one of three forms, and ask two or three things, not nine.
  *Hazard:* what usage of X is unsafe, and what that looks similar is correct?
  *Contract:* what does X guarantee, return and lock; what must a caller have
  done first? *Orientation:* where does X live and what does this tree call it?
- **Ask about the class of bug, not the instance.** No commit SHAs, dates, author
  names or "since v6.x". Do not describe the patch that was missed.
- **Never put the answer in the question.** The question is a probe of what
  models believe; if it states the fact, every model gets it right and the guide
  will say nothing.
- Never ask for an inventory (which fields, which callers, which options).
- Give it `## <prefix>.<id>: <Title>` with a title that names the thing in two to
  five plain words, `- section:` equal to the name of the `# Part` it sits in,
  `- relevance: N - <why a reviewer needs it>`, and a "Start from `name()`"
  pointer to a function or file that exists in the tree.
- When sharpening, keep the question's id and change as little of its text as
  will make it ask for the missing thing.

### 3d: Validate

- `<prompt_dir>/scripts/lint-questions.py <prompt_dir>/subsystem/questions/<guide>.md`
  must exit 0.
- The built guide `<prompt_dir>/subsystem/<guide>.md` is unchanged.
- Nothing in the question names a commit, a model or a local path.

The guide does not change until it is rebuilt with
`<prompt_dir>/scripts/rebuild-guides.sh --tree <linux> <guide>`. Do not run that:
say in the report which guides need rebuilding.

## Step 4: Write Report

**Always** create `./failed-review-report.md` with the following structure:

```markdown
# Failed Review Report

## Reviewed Commit
- **SHA**: <sha>
- **Subject**: <subject>

## Actions Taken

### Bugs classified as `missing subsystem knowledge`

<For each such bug:>

#### Bug N: <short description>
- **Question file**: <path to question file> (question `<id>` added | sharpened); guide needs rebuilding
- **Section**: <section title added or appended to>
- **Summary**: <1-2 sentence description of the knowledge added>

<If none: "No bugs in this category.">

### Bugs classified as `process error`

<For each such bug:>

#### Bug N: <short description>
- **Classification**: process error
- **Rationale**: <from review-failed.md>
- **No prompt changes made.** Process errors indicate the existing prompts
  cover this pattern but it was not applied correctly during analysis.

<If none: "No bugs in this category.">

### Bugs classified as `other`

<For each such bug:>

#### Bug N: <short description>
- **Classification**: other
- **Rationale**: <from review-failed.md>
- **No prompt changes made.** This bug requires runtime validation,
  hardware testing, or analysis beyond the current review architecture.

<If none: "No bugs in this category.">
```

Write this file to `./failed-review-report.md`.

## Final Output

```
================================================================================
FAILED-REVIEW COMPLETE
================================================================================

Reviewed commit: <sha> <subject>
Total missed bugs: <count>
  missing subsystem knowledge: <count> (questions added or sharpened)
  process error: <count> (no changes)
  other: <count> (no changes)

Guide changes:
  <path>: <question id added/sharpened> | "no question changes"

Report: ./failed-review-report.md
================================================================================
```
