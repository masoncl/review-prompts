# Subsystem guides

## How to read a guide

A guide does not explain its subsystem. **Every line of every section states
one of two things: a fact about the kernel tree that differs from what a model
is likely to believe, or a fact that a model is unlikely to know.** Each line
was found by asking several models the same questions, which the models
answered from memory, and comparing their answers with the code.

- **Read a statement as a correction.** "`MAX_CALL_FRAMES` is 16" is there
  because models say 8.
- **A name in backticks exists in this tree.** A name without backticks, as
  in "there is no pte_uffd_wp() here", is a name that models use and that
  does not exist in this tree. The name in backticks beside it is the one
  this tree uses.
- **Where a guide says nothing, you are probably right.** A guide is not a
  complete account. You have the source open, so a guide tells you what you
  would not find by looking, or would not think to look for.
- **`**Unsafe usage**:` marks a usage that breaks**, usually with no error or
  warning. The bullets under the label give the usage that looks similar and
  is correct. The build found no code in this tree that uses it this way and
  could be shown safe.
- **`**Potentially unsafe usage**:` marks a usage that breaks in one case and
  is safe in another.** Code in this tree uses it safely. The bullets under
  the label say which case is unsafe, which is safe, and why. Work out from
  the code which case you are looking at. The usage alone is not a bug.
- **A guide is a list of answers.** Each answer has a title and holds a short
  list of facts, and the answers are grouped in sections. The index points at
  the line of each title.
- **Each section covers one subject.** The last section, "Model gaps", holds
  the corrections that fit none of those subjects. "Model gaps" is short
  because every correction that fits a subject is in the section for that
  subject. Every other section holds corrections too.
- **A guide describes the tree it was built from** and nothing else. The
  guides are in `build/linus/`, and `kernel-version.yaml` in the same
  directory gives the release and the commit of that tree.

This explanation is not repeated inside any guide, since it is the same for
all guides.

## How guides are made

The guides are build output. `kernel/scripts/build-guides.py` produces each
one from the questions in `kernel/subsystem/questions/<guide>.md`:

1. Several models answer the questions from memory.
2. A model answers them again against a kernel tree, and keeps only where the
   first answers were wrong, disagreed, or had nothing to say.
3. Separate model runs check the answers against that tree, section by
   section and then the guide as a whole.

One build of all the guides is made from one kernel tree, and goes into
`build/linus/`. That tree is the most recent tree of Linus's that was
scanned, so `linus` is not the name of a release. A build from a newer tree
replaces the guides there, and `kernel-version.yaml` records the new release
and commit.

`build/` can hold other build directories beside `linus`, such as one for a
stable series. Each has its own `kernel-version.yaml`.

A review does not load every guide. It chooses the build directory whose
kernel best suits the tree under review, or uses the build that its prompt
names. It searches the `subsystem-guide-index.txt` in that
directory for the symbols that a patch touches, and reads the answers that the
search finds. `subsystem.md` says how, and lists the few guides that a review
loads whole.

**Never edit anything under `build/` by hand.** If something in a guide is
wrong or missing, fix or add the question and rebuild. See "Converting a
guide" and "Rebuilding" in `kernel/docs/subsystem-questions.md`.

The built guides replaced hand-written guides, which remain only in the git
history of this repository. Five guides are still written by hand, since they
have no questions yet: `fuse.md`, `hwmon.md`, `leds.md`, `media.md` and
`mfd.md`. They are in this directory, and a review loads them whole.

## What is in this directory

| Path | What it is | Written by |
|---|---|---|
| `build/linus/` | the built guides, from the most recent tree of Linus's that was scanned | the build |
| `build/linus/<guide>.md` | a guide | the build |
| `build/linus/answers/<guide>/<id>.md` | the final answer to one question, exactly as it went into the guide | the build |
| `build/linus/kernel-version.yaml` | the kernel the whole build was made from and checked against: the release and the commit | the build |
| `build/linus/races.md` | the race-tracing method, copied from `verbatim/races.md` | the build, from a hand-written file |
| `build/linus/subsystem-guide-index.txt` | the index a review searches: one line for each answer, with its guide, line, source file and symbols | the build |
| `subsystem.md` | how to choose the build directory and search its index, and the table of the guides that a review loads whole | hand |
| `fuse.md`, `hwmon.md`, `leds.md`, `media.md`, `mfd.md` | guides that have no questions yet. No build makes them and no index covers them | hand |
| `subjective-review.md` | the prompt for reviewing code quality. It is not a subsystem guide | hand |
| `README.md` | this file | hand |
| `questions/` | the question files | hand |
| `verbatim/` | text that a build inserts unchanged | hand |
| `questions/catalogue/<guide>-measurement.md` | a wide set of questions about the subject, used to find out what the models already know | whoever added the guide |
| `questions/catalogue/<guide>-measurement-results.md` | the results of asking the models those questions from memory. They explain why the guide has the questions it has | whoever added the guide |

- **`answers/`** lets `build-guides.py --render-only` assemble a guide again
  without a model. `check-built-guide.py` checks that a guide is identical to
  the guide assembled from its answers, so the check fails after a hand
  edit.
- **`kernel/scripts/rebuild-guides.sh`** rebuilds a guide and installs it in
  the build directory only if `check-built-guide.py` passes. With `--all` it
  replaces every guide. It rebuilds one guide only from a tree at the release
  that the directory records. See
  "Rebuilding" in `kernel/docs/subsystem-questions.md`.
- **`kernel/scripts/make-guide-index.py`** writes `subsystem-guide-index.txt`.
  The index holds the line number of every answer, so `rebuild-guides.sh`
  makes it again whenever it installs a guide.
- **`kernel-version.yaml`** is the only place a commit id appears.
- **`races.md`** is not built by a model. The build copies it so that a build
  directory holds every guide a review can load.
- **A section titled "What the architecture specification says"** holds text
  that the build inserts from a hand-written file under `verbatim/`. No model
  wrote that text.
