# Notes for agents working in this repository

This repository holds prompts for AI-assisted code review. It holds no code
to review. A change here changes what a reviewing model is told.

Get the facts right before you improve the wording. One wrong sentence in a
subsystem guide causes a wrong review of every patch whose review loads the
guide.

In this file "the kernel tree" is the Linux source tree that a guide was built
from, and "this repository" is the one you are in.

## Where things are

| Path | What it is |
|---|---|
| `README.md`, `kernel/README.md` | What the prompts are and how a review loads them |
| `kernel/review-core.md` | The file a review reads first. It names the other files a review loads, and when |
| `kernel/subsystem/subsystem.md` | How a review finds what the guides say about a patch: how to choose the build directory, how to search its index, and a short table of the guides that are loaded whole |
| `kernel/subsystem/README.md` | What a subsystem guide is and how to read one |
| `kernel/subsystem/build/linus/` | The built guides, from the most recent tree of Linus's that was scanned. `linus` is not a release: `kernel-version.yaml` says which release that was. Everything in the directory is build output |
| `kernel/subsystem/build/linus/*.md` | The guides a review loads |
| `kernel/subsystem/build/linus/subsystem-guide-index.txt` | The index a review searches: one line for each answer, with its guide, line, source file and symbols |
| `kernel/subsystem/build/linus/answers/` | The answers the guides are built from |
| `kernel/subsystem/build/linus/kernel-version.yaml` | The release and the commit that the whole build was made from |
| `kernel/subsystem/questions/` | The questions the guides are built from. Written by hand |
| `kernel/subsystem/verbatim/` | Text that a build inserts unchanged: the race-tracing method, which the build copies to `races.md`, the wording of a specification, and the conventions that the maintainers of a subsystem ask for. Written by hand |
| `kernel/agent/` | The prompts a model follows to review a patch or to build a guide |
| `kernel/docs/subsystem-questions.md` | How guides are built, how to write a question, how to rebuild, how to add a guide |
| `kernel/docs/writing-style.md` | How to write prompts, questions, docs and commit messages here |
| `kernel/docs/convert-guide-agent.md` | Instruction sheet for an agent that adds a guide |
| `kernel/docs/reorganise-questions-agent.md` | Instruction sheet for an agent that reshapes question files |
| `kernel/docs/retitle-questions-agent.md` | Instruction sheet for an agent that fixes headings |
| `kernel/docs/read-built-guides-agent.md` | Instruction sheet for an agent that reads the built guides before a release |
| `kernel/scripts/build-guides.py` | Builds a guide |
| `kernel/scripts/rebuild-guides.sh` | Rebuilds guides and installs the ones that pass, into the build directory of the tree's release |
| `kernel/scripts/check-built-guide.py` | Checks a built guide before it is committed: the guide matches its kept answers, its kernel is recorded, and nothing names a model |
| `kernel/scripts/lint-questions.py` | Checks a question file |
| `kernel/scripts/make-guide-index.py` | Writes `subsystem-guide-index.txt` from the guides and a kernel tree. `rebuild-guides.sh` runs it after it installs a guide |
| `kernel/scripts/compare-runs.py` | Compares several measurement runs. A measurement run asks models the questions from memory and checks their answers |
| `systemd/`, `iproute/`, `nfs-utils/`, `pahole/` | The same structure for other projects |

Everything under `kernel/subsystem/` is written by hand, except what is under
`kernel/subsystem/build/`.

The build directory holds the guides of one kernel. To move to a newer kernel,
build every guide again with `rebuild-guides.sh --all`, which replaces what the
build directory holds and records the new kernel in `kernel-version.yaml`.

For how to rebuild and install guides, see "Rebuilding" in
`kernel/docs/subsystem-questions.md`.

Read these first:

- `kernel/docs/subsystem-questions.md`, before you touch anything under
  `kernel/subsystem/`
- `kernel/docs/writing-style.md`, before you write or reword a prompt, a
  question, a doc or a commit message

## What a guide is

- **A guide does not explain the kernel code.** It states where the kernel
  tree differs from what the models that read the guide believe:
  - what the models have wrong
  - what the models disagree on
  - what the models have never heard of

  Where the models are right, the guide says nothing. Read the opening of
  `kernel/docs/subsystem-questions.md` before you decide that a guide says
  too little.
- **A guide names what to look up. It does not copy what a search finds.** It
  says what the lookup will not tell you. It holds no lists of fields,
  callers or options, since a search produces those.
- **A name in backticks exists in the kernel tree.** A name without backticks
  does not exist in that tree.
- **Every answer is a short bulleted list**, so a person can review a guide
  or an answer.
- **Every section lists what the models have wrong about one subject.** The
  last section, "Model gaps", holds what fits none of the subjects. A title
  names the subject of its answer, not the mistake.
- **A guide and an answer have no length limit.** A question has no
  `- words:` field. Length is never a reason to drop a question. A question
  is dropped only if the models already know the answer, or if the answer
  would not change a review.
- **Nothing rewrites a guide after it is checked.** A build stage that
  shortened checked text was tried and removed, because the shortening
  changed what statements meant.

## Rules for guides

- **Everything under `kernel/subsystem/build/` is build output: the guides,
  `answers/`, `subsystem-guide-index.txt` and `kernel-version.yaml`. Never edit
  it by hand.** The facts in a guide come from the questions in
  `kernel/subsystem/questions/<guide>.md`, answered against one kernel tree.
  The guide for every subsystem is committed under
  `kernel/subsystem/build/linus/`, and the same model builds all of them.
- **A build checks each guide twice**, section by section and then as a
  whole. When a check changes a guide, the build checks the changed text
  against the kernel tree.
- **When a guide is wrong or lacks a fact, change the question, not the
  guide.**

  | The problem | The fix |
  |---|---|
  | a guide states something wrong | fix the question or the prompt, or rebuild. Never patch the guide |
  | a review missed a bug because the guide lacked a fact | follow `kernel/agent/failed-review.md`, which adds a question or makes one more exact. Then rebuild |

- **Don't copy facts from the old hand-written guides.** The ones that a
  built guide replaced were deleted from this repository and remain only in
  its git history. Most were never checked against current sources. To add
  a guide, follow `kernel/docs/convert-guide-agent.md`.
- **Check against a kernel tree, not from memory.** Check every function,
  file, lock and return value that a guide names. Finding a name mentioned
  somewhere is not enough. Each name has to be defined where the guide says
  it is.
- **No commit or blob SHAs, and no "since vX.Y"**, in a question or a built
  guide. A guide describes only the kernel tree it was built from, and a
  cherry-picked commit gets a new SHA. Name a commit by its subject line if
  you must. The only place a commit SHA belongs is `kernel-version.yaml` in a
  build directory, which the build writes.
- **Keep by hand the text that no kernel tree can supply, and have the build
  insert it. Don't drop it.** Such text is a method, such as the race-tracing
  method, the wording of a specification, or a convention that the
  maintainers of a subsystem ask for, such as the form of a commit subject.
  It lives in
  `kernel/subsystem/verbatim/`, and a verbatim item in a question file
  inserts it into a guide. See "Text a build inserts" in
  `kernel/docs/subsystem-questions.md`.
- **Don't state a likely kernel bug as a fact in a guide.** A reader treats
  what a guide says as correct behaviour. Write a rule for the usage, or
  leave it out.

## Rules about unsafe usage

Before you write "must" or "always", or call a usage unsafe, search the
kernel tree for code that breaks the rule. If correct code breaks it, the
rule lacks a precondition.

| The search finds | The guide writes |
|---|---|
| no code that breaks the rule | `**Unsafe usage**:` |
| code that breaks the rule, and the code shows why that is safe | `**Potentially unsafe usage**:`, with the unsafe case and the safe case |
| code that breaks the rule, and nothing shows that is safe | `**Unsafe usage**:`. That code may be a bug, so it is not used as an example |

- In a question, ask for the requirements of safe usage, as in "what are the
  requirements for buffers passed into `x_send()` in order to assure safe
  usage?". Don't ask what usage is unsafe.
- A rule needs evidence in the kernel tree: the code that defines the
  requirement, or the line that fails when the usage happens. What a model
  remembers is not evidence.
- A safe example names what defines the requirement. A driver that works does
  not prove that what it does is enough.
- A guide describes how code must be used. It does not tell a reviewer what
  to report.

## Rules for this repository

- **This repository is public.** Nothing committed names a model or gives the
  cost of a run. Call the models "reader A", "reader B" and so on. Keep run
  reports out of git.
- **Load order.** A review reads `kernel/false-positive-guide.md` only after
  the review has identified a suspected bug. That file may refer to
  `kernel/callstack.md` and to the subsystem guides. Those files never refer
  to `kernel/false-positive-guide.md`.
- **Every commit carries a `Signed-off-by:`** with a real name and email
  address.
- **Write plainly.** Use ordinary words, open an instruction with the action,
  and put a rule that has cases in a table. See
  `kernel/docs/writing-style.md`.
- **When you reword a prompt**, compare it with the old text one instruction
  at a time, and keep every output format the same.
- **Read every sentence you add to a prompt before a build uses it.** Check
  each new sentence against this list. Then show the diff to the maintainer.

  | Check | Instead of | Write |
  |---|---|---|
  | one negative at most | "never write a bullet that no draft does not contradict" | "write a bullet only where a draft is wrong" |
  | no figure of speech | "has no place in the answer" | "delete the bullet" |
  | three nouns in a row at most | "the number of the line of the differences" | "the number of its line" |
  | one term for one thing | "claim" here, "statement" there | "claim" in both places |
  | one example for each rule | the rule alone | the rule, then a short example of the output |
  | each instruction once | an instruction that the prompt already has | search the prompt first; if the instruction is there, add nothing |
