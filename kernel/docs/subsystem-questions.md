# Building subsystem guides from questions

The subsystem guides under `kernel/subsystem/build/linus/` state facts about
the kernel tree they were built from:
which function takes which lock, what a helper returns, which pattern is a
bug. The kernel changes, so those facts go stale. Searching a guide for names
that no longer exist finds only part of the damage. A line by line review of
the six hand-written MM guides against one tree found three other kinds:

- rules stated as absolutes that correct in-tree code contradicts
- lists that looked complete and were not
- mechanisms that had been reworked while every name stayed the same

So the guides are built, not maintained. Each guide has a file of questions.
People write the questions and keep them, and the questions stay the same over
time. A build puts each question to a model that can read one kernel tree, and
writes the answers, in order, into the guide for that tree:

```
guide(tree) = the answers to its questions, asked of that tree
```

Run it on mainline, on a stable tree with backports, or on a vendor tree, and
you get the guide for that tree.

The questions are not an attempt to recreate the hand-written guides. Those
were mostly lists of things that went wrong once. An old guide is one input
for knowing which hazards have actually bitten, and nothing more.

## What a guide is

- **A guide does not explain the kernel code. It states the difference between
  what the models that read it believe and what the tree does.** The readers
  already know a lot, from the kernel versions they were trained on, and they
  have the tree open when they review. They cannot tell which of their beliefs
  have stopped being true, which never were, or what they have never heard of.
- **A build asks the readers first.** Each reader answers every question from
  memory. The builder has the code in front of it and writes only the
  difference:
  - what a reader states that is wrong here, and what is true instead
  - what readers disagree about
  - what they left blank
  - what the question asks for that none of them supplied

  Where every reader is right, the guide says nothing. That gives the five
  lines a reviewer needs, not twenty bullets about how the code works.
- **A guide adds to the sources. It does not replace reading them.** An answer
  that points at a function and says the one thing about it that is easy to
  miss is worth more than a paragraph that describes the function. The reader
  can open the function.
- **People have to be able to review a guide.** An answer is a short bulleted
  list with one fact per bullet and the name or the condition first, or a
  table where several things share the same attributes. Nobody can check a
  paragraph of eight claims against the source. Eight lines can be checked.
- **The readers already know a good deal.** Asked about VMAs with no sources, a
  current model describes the concepts and the architecture correctly and gets
  nine names in ten right. It gets these wrong:
  - what moved recently: names, layouts, which file a function is in
  - a score or so of facts that would change a verdict
  - the things it says plainly it does not recognise

  The guide covers those three things, and the build finds them by asking the
  readers first.
- **A guide says how the tree is.** It never tells a reviewer what to report
  or not to report. See "Instructions don't belong in a guide" below.
- **A likely kernel bug is not a fact for a guide.** A reader treats what a
  guide says as correct behaviour. The builder writes the pattern as a rule,
  or leaves it out.

## What decides the size of a guide

**The cost that matters is loading the guide, not building it.** A guide is
read into a reviewer's context on every patch that touches the subsystem, so
length is a cost. How many model runs a build takes does not matter.

**A word count never decides what a guide leaves out.** A question is left out
of a build set for one of two reasons only:

- every reader already answers it correctly
- the answer would not change a review

Every reader, not most. A guide is written for the weakest of its readers, and
the list of readers given to a build says who the guide is for. To write a
guide that assumes more, measure with stronger readers. The measurement phase
finds out what each reader already answers correctly.

Everything else that matters to a review goes in, and the guide is as long as
that makes it. If a guide grows too big to load, split it, as the race-tracing
method was split from the locking guide.

**No number says how long an answer or a guide should be. Once text has been
checked, nothing rewrites it except to fix what is wrong.** The builder writes
the difference, the section check verifies it, and a read of the whole guide
makes it accurate. That is the guide. What keeps it short is what the builder
is asked for, not an editor afterwards. There is:

- no `- words:` field
- no send-back for running long
- no limit on the length of what the read of the whole guide hands back
- no size check

Nothing in the build or its checks refers to the hand-written guides either.
See "What was tried" for why.

**What a tree cannot answer is kept by hand, not dropped.** A method for
tracing races, or what an architecture specification says, cannot be read out
of the source. A build that silently leaves it out is not a full substitute
for the guide that had it. Such text lives in a file kept by hand, and the
build inserts it as it is. See "Text a build inserts".

## Question files

There is one markdown file per guide,
`kernel/subsystem/questions/<guide>.md`:

```markdown
# Questions: MM VMA Operations

- guide: mm-vma.md
- title: MM VMA Operations

# Locks and page tables

## vma.vma-lock-only-operations: Per-VMA-lock-only paths

- section: Locks and page tables
- relevance: 5 - whether any of these can free a page table is the fact models get backwards

What may an operation that holds only a per-VMA read lock do to page tables: can any of them free
a page table, through which functions, and what do the rest restrict themselves to? Start from
the callers of `lock_vma_under_rcu()` and `lock_next_vma()`, and `mm/madvise.c`.

## vma.write-lock-usage: mmap write lock and tables

- section: Locks and page tables
- relevance: 5 - the race has shipped, and nothing in a diff shows it

What usage of page table state by code that holds the mmap write lock is unsafe, and which
in-tree code that touches page tables under it without write-locking the VMA is correct? Start
from `collapse_huge_page()`, `kernel/events/uprobes.c` and `mm/ptdump.c`.
```

That is from `kernel/subsystem/questions/mm-vma.md`. `mm-pagetable.md` beside
it is the fullest worked example.

| Part of the file | What it is |
|---|---|
| a top-level heading other than `# Sections` and `# Quick checks` | starts a **part** of the guide, which is a subject |
| `## <id>: <title>` | one question. The id never changes |
| `- section:` | optional. Consecutive questions that name the same section go under one heading |
| `- relevance:` | 0 to 5, with a one-line reason |
| `- group:` | optional, for quick checks that belong together |
| `- drafts: all` | optional, and `all` is the one value it takes. The builder gets every draft for every question in the guide |
| `- verbatim:` | names a file to insert in place of an answer |
| `- min-relevance: 3` | in the header. Build this guide from questions at that relevance and up |
| the text under the fields | the question, in plain prose |

- **Parts.** The page table guide has "Main structures" and "Where to look",
  then one part for each thing it is about (non-present entries, the callback
  walker, batching, freeing tables), then "Model gaps". The sections after a
  part heading render beneath it. A part that has only one section renders
  without that section's heading, since the part's own heading already says
  where the reader is.
- **The id** names the answer file and is what `--only` takes.
- **The title** becomes the section heading, or the bold name of a quick
  check.
- **Relevance** says how much the answer helps someone reviewing a patch. See
  "Relevance".
- **A section** is how a big topic is covered: several small questions, not
  one large one. Each question renders as its own title in bold, followed by
  a short bulleted list. The model gets a section's questions together.
- **A group** label is not rendered. It only says which questions are
  answered and checked as one, as in
  `- group: results of merge and modify`.
- **`- drafts: all`** is on the "Model gaps" question.
- **The question** asks two or three things at most.
- **Order in the file is order in the guide.**
- **No field says how long an answer is.** An old file's `- words:` line is
  read and ignored.
- **`# Sections` and `# Quick checks`** are two special top-level headings.
  Questions under `# Quick checks` render as bullets under "Quick Checks", and
  questions under `# Sections` render as sections. No build set uses either
  now.

### Text a build inserts

An item may name a file to insert, in place of a question to answer:

```
## gicv3.spec-list-registers: What the architecture specification says

- section: List registers
- verbatim: ../verbatim/gic-v3-list-registers.md
```

It takes a section and nothing else. On every build the text of the file goes
into the guide under that title, exactly as it is:

- no model writes it
- no model is shown it
- no check is shown it, even among the other answers of the guide
- its words count towards the size of the guide

The files live in `kernel/subsystem/verbatim/` and are kept by hand. The five
for `gic-v3` were copied byte for byte from the hand-written guide.

The same way keeps what the maintainers of a subsystem ask for and no code
states, such as the form of a commit subject. `hwmon`, `i2c`, `leds`, `mfd`
and `rust` each have a file `<guide>-conventions.md`, inserted under the title
"Conventions for new code".

- Such a file states each convention once, and leaves out what tells a
  reviewer what to report.
- A convention that holds only for new code says so.
- After you add or change such a file, render the guide again with
  `--render-only`, as "Answers are kept" says, and make the index again. No
  model runs.
- `kernel/subsystem/subsystem.md` has a table that sends a review to these
  answers by directory. Add a row there when a convention applies to every
  patch in a directory, since a search of the index by symbol can miss it.
  The convention for `i2c` names `struct i2c_device_id`, so a search finds
  it, and a review loads `rust.md` whole. Neither needs a row.

A whole guide can be kept by hand the same way. A question file whose header
has `- verbatim: ../verbatim/races.md` and no questions builds to a copy of
that file. That is how the race-tracing method, split out of the hand-written
locking guide, becomes `races.md` in a build directory.

A question file can arrive in a patch, and the file it names ends up in a
guide. So the driver restricts the name. It must be:

- a relative path to a `.md` file
- inside the directory above the question file
- free of symbolic links
- no larger than 200 KB

The lint refuses anything else, and so does the driver before it starts.

## Writing a good question

The answer is only as good as the question, so all the care goes here.

### What to ask

- **Start from the subject, not from the old guide.** Survey these first:
  - what the thing is, and where instances live
  - its life from creation to free
  - which lock protects what
  - how code that uses it must behave
  - what someone changing the implementation must preserve: the invariants,
    the order of operations, what is undone on failure, the other builds and
    tests that share the code

  The questions come from that survey. They do not ask for the survey.
- **Ask in one of three forms.** There is no fourth.

  | Form | Asks |
  |---|---|
    | Requirement | what are the requirements for X in order to assure safe usage |
  | Contract | what X guarantees, returns and locks, and which of several similar functions is used when |
  | Orientation | where X lives and what this tree calls it |

- **Don't ask for a list that one search would produce.** The reader has the
  tree open and can search it. So a guide names what to look up, and says
  what the lookup will not tell you. "Which fields", "which options", "which
  callers", "which architectures" and "list the functions" all ask for such a
  list. Fold them into a contract question as "and where to find the rest", or
  drop them. A table is for variants a reader has to choose among, or an
  enumeration whose values change what code must do. It is not for the members
  of a structure.
- **Ask what a reviewer would get wrong.** Don't ask how something works
  inside.
- **Ask for what the code requires, not for what each implementation does.**
  "Which fields does the callback read, and so what must be set before the
  call?" gets the contract. "At what point in its init does each scheduler
  make the call?" gets a description of each one, and if one of them has a
  bug the guide states the bug as a fact.
- **Ask for what a reviewer needs, not for completeness.** "The helpers a
  driver is likely to call", not "every helper in every API".
- **For a rule, ask for the requirements.** "What are the requirements for
  buffers passed into `x_send()` in order to assure safe usage?" The builder
  then has to find where the tree defines each requirement, and a rule follows
  from a requirement. Don't ask "what usage is unsafe". That asks for a list
  of bad things, and the builder offers whatever the readers remember, with
  one driver that seems to get away with each. See "Rules and their labels".
- **Measure before you ask.** Run the wide set of questions with no sources
  first. Drop, or shrink to a pointer, what the readers already answer
  correctly.

### How to ask it

- **One question asks two or three things, not nine.** Each thing asked gets
  its own bullets in the answer. A question that asks eight gets a wall of
  compressed clauses, and gives the checker thirty statements to verify. Split
  it, or keep the two a reviewer would act on. The lint flags a question with
  more than three question marks.
- **Ask about the concept, and offer names only as a starting point.** "The
  function that maps a fresh anonymous folio in the fault path", then "start
  from `do_anonymous_page()`". A rename must not break the question, and on an
  older tree the name may be different.
- **Never put the answer in the question.** The question has to make sense on
  a tree where the answer is different. That rules out:
  - offering candidates: "for example a plain memory barrier or no barrier",
    or "which inputs: the VMA, the memslot alignment, dirty logging"
  - saying what a reader expects: "where a reader expects an untyped pointer"
  - presupposing the rule the question is asking about
- **Never make the builder resolve a conflict.** A question that asks about
  the state of a structure and then says "do not list its members" is wrong.
  Ask something that can be answered without them.
- **Ask about the code, not about its comments.** "What does each guarantee
  according to the comments at its call sites" sends the builder and the
  checker to a comment for evidence, and they come back with what the comment
  says. A comment may be where to start. It is never what is asked for.
- **Say what to do when the feature is absent.** "If this tree has no per-VMA
  locks, say so and stop."
- **No commit SHAs, and no "since v6.x".** A cherry-pick changes a SHA. On the
  tree being asked about, the code either does the thing or it does not.
- **Say nothing about the form of the answer.** "A table of", "give names in
  full" and "one phrase each" belong in the builder's instructions, which
  already say them. A question that is only such an instruction has no
  question in it.
- **Say nothing about length.** A question has no word count. If an answer
  would sprawl, the question asks several things, or asks for a list that one
  search would produce. Split it, or ask for the rule and where to find the
  sites.

### Titles

A title and the name of its subject are all a reader sees when it decides
whether an answer is worth reading.

- **The title and the name of the subject each name the thing**: the
  function family, the structure, the lock or the flag, in plain words that
  someone would search for.
- **It is a noun phrase of two to five words**: "Detaching a VMA", "Merge
  conditions", "Flag helpers". It is not a clause that restates the question,
  such as "What detaching a VMA waits for".
- **It does not describe the mistake.** "Zones that count" says nothing until
  the answer has been read. "Zones in balance checks" says whether to read it.
- **Prefer plain words to a kernel identifier**, which a rename breaks. Use
  the identifier where it is the word someone would search for.
- **It does not repeat the subject it is under.** The lint refuses that.
- **A question goes under the subject whose code it is about.**

Titles are paid for on every load, like everything else in the guide. The lint
flags a title that starts with a question word or runs past six words.

The first part of every build set is "Main structures". Its answer holds what
the readers have wrong about the main objects and how they relate. It is not a
description of them. Give it a title that names what it holds.

### The lint

`kernel/scripts/lint-questions.py` checks the format:

- the header, the heading and the fields
- a question that does not ask too many things
- no repeated ids
- no SHAs or version history

`--table` lists the questions in a file by relevance.

## Relevance

Not every question earns its cost. Relevance says how much the answer helps
someone who is about to use the subject, change it, or review such a change.

| Score | Meaning |
|-------|---------|
| 5 | Nothing else makes sense without it, or getting it wrong is a recurring bug class that a competent reader would not see in the diff. |
| 4 | Needed by most people who use or change this code, with facts specific to the tree. |
| 3 | Real and useful, but confined to a few files, or partly caught by lockdep, asserts or the compiler. |
| 2 | Narrow: a handful of call sites, one configuration, or a lesson from one or two fixes that might recur. |
| 1 | One fix written up as a rule, or something anyone working on that code already knows. |
| 0 | Generic coding sense, or obsolete. |

The score is about how much the answer helps, not about how bad a bug would
be. `--min-relevance N` (default 2) skips everything below N. Low scorers stay
in the file with their reason, so dropping them is a recorded decision.

## Rules and their labels

A guide describes how the code must be used. It does not tell anyone what to
report. The old guides had `REPORT as bugs` lines. A built guide has rules,
each labelled and followed by the usage that looks similar and is correct.

**A rule needs evidence in the tree.** A rule starts as a belief: a reader
remembers that some usage is unsafe. That is not evidence. The builder writes
a rule only if it found one of these in the tree:

- the code that defines or checks the requirement that the rule rests on
- the line of code that fails, frees or corrupts when the usage happens

**A safe reason names what defines the requirement.** A driver that works does
not prove that what it does is enough. One guide gave `____cacheline_aligned`
as what makes an embedded DMA buffer safe, because one driver uses it. The
alignment that DMA needs is `ARCH_DMA_MINALIGN`, which is larger on some
architectures. The safe bullet has to name what defines the requirement, and
the checker checks the example against that definition.

Before a rule is written, the builder searches the tree for code that does
what the rule would call unsafe. The section check does the same search again.
The label says what they found:

| The search finds | Label |
|---|---|
| no code that does it | `**Unsafe usage**:` |
| code that does it, and the code shows why it is safe there | `**Potentially unsafe usage**:` |
| code that does it, and nothing shows that it is safe | `**Unsafe usage**:` |

- **`**Potentially unsafe usage**:`** describes the unsafe usage and the safe
  usage under it. A reviewer works out which case a change is in.
- **Code that nothing shows to be safe** may be a bug, so it is not used as an
  example. Finding that something is done is not finding that it is right.
- **The search is for the effect**: the field written, the call made without
  the test, the lock not taken. A search for callers of one helper misses
  code that does the same thing by hand.
- **The checker searches the same section first.** In about half of the rules
  that were too broad, the code that contradicted the rule was described a few
  bullets away.

The labels are two and three words long because every rule in a guide repeats
them.

## Building

```
kernel/scripts/build-guides.py --tree <linux> --out <dir> [--guide mm-vma ...]
        [--min-relevance 2] [--only <id> ...] [--jobs 8] [--model <name>]
```

The driver puts the questions at or above the threshold into groups. The
questions of one section form a group, since a section is one subject. Any
other question is a group of its own. The driver splits a group of more than
twelve questions (`--group-questions`) into even parts. Then:

```
ask the readers from memory  ->  answer every group  ->  check every group
    ->  correct the whole guide  ->  write
```

| Stage | Prompt | What it does |
|---|---|---|
| Ask the readers | `kernel/agent/answer-from-memory.md` | each reader answers every group with no sources and no tools |
| Answer | `kernel/agent/answer-question.md` | the builder writes the difference between the drafts and the code |
| Check | `kernel/agent/check-answer.md` | an independent run checks each group against the tree. A group that the check changed is checked once more |
| Correct | `kernel/agent/correct-guide.md`, `check-corrections.md` | one run reads the whole guide, and another checks its edits |
| Write | | the final text goes into the guide |

Up to `--jobs` groups run at once. The driver asks again for a question that
a reply skipped.

### Ask the readers

Each reader is a model that will read the guide. Name them with
`--reader-model`, which can be repeated. With none named, the builder is the
reader.

- What a reader says is kept in `answers/<id>.memory.md`. With several
  readers the files are `.memory1.md`, `.memory2.md` and so on, in the order
  the readers were given.
- The builder gets the drafts unchecked.
- `--no-memory-pass` skips this stage.

### Answer

There is one model run per group. The builder investigates the subject once,
in depth. For each question it writes only the difference between what the
readers said from memory and what the code does.

- **Where a reader was right**, the builder does not say it again, or gives
  only the place to look.
- **Where a reader was wrong, out of date or blank**, the answer corrects it,
  down to "there is no old_name() in this tree; `new_name()` does that". The
  absent name is plain text, since backticks are only for what exists in the
  tree.
- **Length has no limit.** The builder writes a line or two where the readers
  are nearly right, and more where they are badly wrong.
- **A draft is not an outline.** The builder does not copy the length, the
  order or the detail of a draft.
- **The difference is measured against the question**, not against everything
  else that is true of the code. If the question asks which lock a function
  holds, a leak on its error path is not a difference.
- **A correction is a line**: the true statement, not the mechanism behind
  it.

The builder writes the comparison down. Before any answer it lists the
differences it found for each question:

```
reader 2: says X; the code: Y
no reader: what the question asks that nobody supplied
all right: what every reader had and is therefore not written
```

It writes each answer from that list and from nothing else. The lists are
kept in `<out>/differences/<id>.md`. They are not part of the guide. They
record exactly how each model is wrong.

The builder writes the whole group, which is everything the guide says about
one subject. So each fact goes to the one question that asks for it, and the
answers agree with each other.

### Check

When every group has been answered, a second, independent run checks each
group. It gets the group's questions and answers and, beside them, every
other answer in the guide.

It goes through its group claim by claim against the tree. It looks hardest
at:

- absolutes
- lists that look complete
- names that merely sound right
- what a function is said to lock or return
- examples offered as the safe form
- conditions left unstated
- code that may be a bug

For "only X does this" it searches for the effect, not just for callers of
the helper.

With the whole guide in front of it, the check also looks for:

- answers that contradict each other
- facts stated twice
- facts under the wrong question

It hands back the group's answers corrected, and a list of what it changed,
with the place in the code where it saw the reason. It fixes and narrows. It
does not add what a question did not ask for.

**A group that the check changed is checked once more**, up to `--checks N`
(default 2). The second check is given the first's corrections and its
reasons, and is told not to put back what a correction deleted unless the code
says otherwise. Before this, a second check twice undid a correction that was
right.

### What counts as checked

The prompts for the builder and the checker rest on one principle, not on a
list of special cases: **try to prove each claim wrong.** Finding something
that agrees with a claim is not enough. Ask what would make the claim wrong in
the tree, then go and look:

- an earlier test that returns first
- a second site without the lock
- a configuration that compiles it out

A comment, kerneldoc or a document is never evidence. It is a claim to check
like any other. Where it disagrees with the code, read the code again and
make an evidence based decision.

A bullet often makes several claims, and the checker writes one record for
each. What it has to look at depends on the kind of claim:

| Kind of claim | What the check needs |
|---|---|
| about one thing | the body of the function |
| about a set | the search that lists every member |
| something is absent | a search of the whole tree |
| something is not done | the function and everything it calls |
| the result of a call chain | every function in the chain |
| a consequence | proof of its own |
| a condition | every enclosing `#if` |

For each claim it lets through, the checker writes down what would make it
wrong, where it looked, and a line of code it saw there. The driver keeps
that under `checked/` in the output directory.

### Facts stated twice

**A fact deleted twice is a fact lost.** The checks of one pass run at the
same time, and each sees the other answers as they were before the pass. One
check deletes a bullet because another answer says the same. The check of that
other answer deletes it there for the same reason. The fact is gone, and every
check passed. Over one build of all the guides there were 85 pairs of answers
where the check of each answer deleted something and named the other answer.

So these rules hold:

- A fact belongs in one answer: the one whose question asks for it. It is
  never deleted from there.
- A check that deletes a repeated fact quotes what it deleted and names the
  answer that has it.
- The driver shows the note to the next check of the answer that was named.
  That check confirms the fact is there, and restores the fact if it is
  missing. A note is reason enough for the driver to check the group again.
- The last pass deletes nothing for being repeated, since no check is left to
  confirm that the other answer has the fact.
- A bullet is deleted one claim at a time. A claim that no other answer makes
  stays.
- The last section check may say something about an answer outside its group.
  No later section check would see that, so the driver passes it to the read
  of the whole guide.

### Correct the whole guide

The section checks never see the guide as a whole. Each works on one section,
in parallel, with the other answers shown beside it.

So one more model, the editor, is then given the rendered guide. It reads the
guide from top to bottom with one concern: whether it is true. `--read-model`
names a different model for this. It looks for:

- contradictions between sections
- a rule undercut by an exception elsewhere
- a list that another answer shows is incomplete
- a claim it would not rely on in a review

It is told not to shorten anything. It hands back the answers it changed, and
one list of everything it has fixed since the first checked version.

A checker then gets three things:

- the guide as it now stands
- that list
- **one diff from the first checked version to now**

It is always that one diff, however many rounds there have been. The checker
confirms every change against the tree. It hands back corrections, each with
its reason, and the editor sees them on its next turn.

The two take turns until one of them changes nothing. `--rounds` caps the
number of turns (default 4, and 0 skips the stage). What comes out is the
guide.

### Write

The final text goes into the guide. The first draft of each answer is kept
next to it, so that the two can be compared.

### Output

| Path | What it holds |
|---|---|
| `<dir>/<guide>.md` | the guide |
| `<dir>/answers/<id>.md` | the final answer to one question |
| `<dir>/answers/<id>.first.md` | its first draft |
| `<dir>/answers/<id>.memory.md` | what a reader said from memory |
| `<dir>/differences/<id>.md` | the builder's list of differences |
| `<dir>/checked/` | the checker's record for each claim |
| `<dir>/run-report.md` | the report of the run |
| `<dir>/failed-calls/` | what a failed or slow call was doing |
| `<dir>/incomplete.txt` | the stages that did not run, if any |

The report gives:

- the version of the tree
- a row for each question: words written, corrections, time
- every correction the checks made
- what the read of the whole guide changed

The report names the models used, so it stays out of git. `--dry-run` lists
what would be asked and shows one prompt.

### semcode

The builder and the checker get the code-query tools of semcode if either of
these is true:

- the user has an MCP server named semcode in their own agent configuration
- `semcode-mcp` is on the path and the tree has a `.semcode.db`

The tools find a function or a type, callers, callees, call chains and what
sits behind a function pointer, and search function bodies. They are pointed
at the database of the real tree.

- The commit-history and mailing-list tools of semcode are denied by name.
  They would bring in exactly the history a guide must not have.
- semcode is an index and can be behind the tree. The prompts say to trust
  the files where the two disagree.
- The tree's own `.mcp.json` is never read. An MCP entry is a command to run,
  and the tree is not trusted.
- The driver prints the exact command it starts.
- `--no-semcode` turns it off.

### Time

A guide takes about twenty minutes. All of them take about four and a half
hours at eight guides at once, when every call behaves.

| Stage | Share of the time |
|---|---|
| asking and answering | a third |
| the two section checks | a third |
| the read of the whole guide, which cannot be split | a third |

Wall time depends on the stages, not on the number of questions, because the
groups run at the same time.

### Calls that stall

One build of every guide took over nine hours. Three calls in a hundred
stalled for close to an hour, and they took nearly half of all the time.

A stalled call is one whose connection to the model has gone idle. The CLI
gives up on the reply after five minutes and asks again, up to ten times,
inside the one call. So the driver watches each call.

- **It counts steps.** It reads the transcript that the CLI keeps of the
  call. A step is the model saying something, the model asking for a tool, or
  a tool answering. A request that the CLI sends is not a step, since a
  stalled call goes on sending them.
- **It stops a call that takes no step for `--quiet` seconds** (default 300),
  together with the code search server the call started, and tries once
  more. In a build of every guide, no working call went longer than two
  minutes between steps.
- **It leaves a working call alone for `--timeout` seconds** (default 3600).
  The second try gets twice that.
- **If the CLI keeps no transcript where the driver looks**, only `--timeout`
  applies, and the log says so. The first call of a build shows whether the
  CLI keeps a transcript there.

A fixed limit of fifteen minutes was tried first. It stopped a section check
that was nineteen minutes of work, which then had to be done again from the
start.

`<dir>/failed-calls/` keeps what a call was doing, for a call that failed or
that took over ten minutes. It holds the times of the events in the session
and the longest waits between them. That shows whether the call was waiting
for the model or for a tool.

### A stage that did not run

A call that fails on its second try as well leaves its stage undone:

- a reader not asked
- a group not answered
- a section not checked
- the whole guide not read through

The guide is still written, so that a person can read it. The build lists
what did not run in `<dir>/incomplete.txt` and exits with an error, and
`rebuild-guides.sh` does not install the guide. A section that was never
checked against the tree is not one to review with.

### Models and modes

- `--model` picks the model that builds and checks.
- `--permission-mode` passes a permission mode through to the model process.
  The read-deny rules and the tools denied by name hold in every mode.

A full build looks like this:

```
kernel/scripts/build-guides.py --tree ~/src/linux --out <dir> --guide mm-vma \
    --min-relevance 0 --model <builder> --permission-mode auto \
    --reader-model <reader> --reader-model <another reader>
```

### Which kernel a guide came from

`--record FILE` writes a small YAML file. It records the release that the tree
is based on, as `kernel:`, and the commit, as `sha:`.

- `kernel-version.yaml` in a build directory is written this way. It holds one
  release and one commit, since every guide in the directory is built from
  the same kernel. It is the only place a commit id appears.
- The build directory is named `linus`, not for a release, since it is rebuilt
  whenever Linus's tree has moved on. Only `kernel-version.yaml` says which
  release the guides are from.

### The builder must not see a guide

An answer copied from an existing guide looks perfect on the reference tree
and is silently wrong on any other. The normal install makes this likely:
`setup.sh` puts a kernel skill in the user's agent configuration, which loads
automatically in a kernel tree and points at this repository. So the driver
starts the model with:

- an empty agent configuration directory: no skills, commands, plugins,
  memory or settings
- file read, search and glob as its only tools. It has no shell. An allowlist
  such as "only `git grep`" is not read-only, since `git grep -O<cmd>` runs a
  command
- a throwaway snapshot of the tree as its working directory, with no `.git`,
  with any agent instruction files the tree carries removed, and with any
  symlink that leads outside the snapshot removed
- read access denied to this repository, the output directory, the user's
  home directory, and `/proc`, `/etc` and the other system directories
- its whole prompt supplied by the driver: the instructions and one group of
  questions

The tree is text written by thousands of people and is not trusted. The model
never writes anything. It prints its answer and the driver writes the file.
The driver scans every reply for credentials before it stores the reply, and
throws away a reply that contains any. A container that mounts nothing but
the snapshot is the stronger form of all this.

Because of the isolation the model process cannot see your login. The driver
finds your credentials and hands over those alone. It looks in this order:

1. an API key, or the Bedrock or Vertex variables, from the environment
2. the `apiKeyHelper` in your settings
3. your stored login. The driver links that one file, and nothing else, into
   the empty configuration directory

The driver makes one trivial model call first, so a credentials problem stops
the run at once.

### Measuring what a model knows

`--no-sources --check-memory --tree <linux>` answers every question from
memory, and then has the checker correct those answers against the tree. The
report gives, for each question, how many corrections were needed and how
much of the answer from memory was rewritten.

That is how to decide which questions earn their place:

| The reader | The question |
|---|---|
| already answers it correctly | needs at most a pointer |
| answers it confidently and wrongly | has to be in the guide |

`--reader-model` names the model whose memory is tested, and `--model` names
the model that checks it, so one checker can measure several readers. Use a
wide set of questions for this, not the trimmed set a guide is built from.
`kernel/subsystem/questions/catalogue/` keeps the wide sets.

### Without sources

`--no-sources` gives the model no tree and no tools, and asks the same
questions about the latest Linux it knows, with
`kernel/agent/answer-from-memory.md`. The guide it writes says at the top
that nothing in it was read from a tree.

It is a baseline. Comparing it with a real build shows what reading the
source buys. A question that the model already answers correctly from memory
is one where the guide adds little.

## Converting a guide

These are the steps that turned `mm-vma` from a hand-written guide into a
built one. The other guides followed the same route. A subsystem that has no
guide yet starts at step 2.

Two question files are involved, and they do different jobs:

| File | What it is | Who loads the result |
|---|---|---|
| the **measurement set**, `catalogue/<guide>-measurement.md` | a wide set of questions that covers the whole subject | nobody. Its only job is to find out what the readers know and what they get wrong |
| the **build set**, `kernel/subsystem/questions/<guide>.md` | the smaller selection that a guide is built from | every review of the subsystem |

### 1. Read the hand-written guide, if there is one

- List what it is trying to teach. `catalogue/mm-vma.md` is such a list.
- Mark what no tree could answer, such as a method or the wording of a
  specification. That goes in a verbatim file, not in a question.
- Its length decides nothing.
- Expect mostly past bugs written as rules, some items that are not about the
  subject at all, and no map of the subsystem.

**Only the six `mm-*.md` guides were ever checked against current sources.**
Treat any other hand-written guide as a list of topics that once mattered,
not as truth. `bpf.md` told reviewers to use two functions that exist nowhere
in the tree.

- Don't word a question so that it presupposes a fact the old guide states.
- Expect the built guide to differ.
- Write down where the old one is stale.

### 2. Survey the code, not the guide

Survey the structures, the files and the functions in them, the state that is
passed around, the callbacks, the locks, and any test build that shares the
source. The questions come from this survey, and so do the names offered as
starting points.

### 3. Write a wide measurement set

Write up to a hundred or so questions. Cover what the thing is, how it is
used, and what a change must preserve. Keep the file in
`kernel/subsystem/questions/catalogue/` as `<guide>-measurement.md`, and lint
it.

### 4. Measure each reader

Measure each model that will read the guide, all with the same checker. Three
readers of different ages have been used so far. They are labelled A, B and C
in everything that is committed.

```
kernel/scripts/build-guides.py --no-sources --check-memory --tree ~/src/linux \
    --questions kernel/subsystem/questions/catalogue --guide <guide>-measurement \
    --min-relevance 0 --checks 1 --jobs 5 --model <checker> --permission-mode auto \
    --reader-model <reader> --out <dir>/know-A
```

- Make one run per reader. Each takes ten to twenty minutes, and they can run
  at once.
- Every question must come back answered.
- If a whole group comes back empty, the reader wrote its answer markers in a
  way the driver could not read. The reply is kept in `<out>/unparsed/`, and
  `--only <ids>` runs just that group again.

### 5. Compare the readers

`kernel/scripts/compare-runs.py a=<dir>/a b=<dir>/b ...` gives the totals
and, for each question, how much of each reader's answer was rewritten.

Then read the corrections in each `run-report.md`. The numbers only say where
to look. Sort what the readers got wrong into three kinds:

| Kind | Notes |
|---|---|
| names and layouts that have moved | the largest kind, and different for each reader. The most current reader carries facts that were true for a few releases and have changed again. An older one has whole mechanisms out of date |
| facts that would change a verdict | |
| things a reader says it does not recognise | |

### 6. Choose the build set

This is `kernel/subsystem/questions/<guide>.md`.

**What to drop and what to keep**

- Drop what every reader already answers, or shrink it to a pointer.
- Drop what would not change a review.
- Keep everything else that any one reader gets wrong. The threshold used so
  far is that the check rewrote half of the answer.
- Don't cut a question to reach a size.
- Don't let the readers who knew outvote the one who did not.
- A question says nothing about length, and nothing is sized against a
  hand-written guide.

**The first part is "Main structures".** It holds one question,
`<prefix>.overview`, which asks what the code is for and what its main
structures are. It does not ask what a function requires or returns, since the
later sections state that and a guide should say each thing once. It is kept
whatever the measurement says, and so is "Where to look", which maps the
files. A guide that opens on a table of fields, without saying what the
structure is, fails as a document.

**The last part is "Model gaps".** It holds one question,
`<prefix>.model-gaps`, with the field `- drafts: all`.

- The builder is given what every reader said from memory for every question
  in the guide.
- It writes one bullet per mistake: the belief first, then what is true in
  this tree and where to see it. The most consequential mistake comes first.
- The section check deletes from "Model gaps" whatever a section already
  says. What is left belongs to no one subject, which is why the part comes
  last.
- The question is the same in every build set, and it is not put to the
  readers.

The measurement finds out how the models are wrong, mostly because the kernel
has moved on since they were trained. A model that is told its memory is out
of date can correct for that. A model that is only given the right fact may go
on trusting its memory everywhere else.

What a guide is and how to read one is said once, in
`kernel/subsystem/README.md`, and not at the top of each guide.

**Organise the rest by subject, not by kind of statement.** After "Main
structures" and "Where to look", make one part for each thing the guide is
about. In the page table guide these are non-present entries, walkers,
batching and freeing tables.

- All the questions of a part name one section, so that they are answered
  together.
- Inside a part, use this order:
  1. what this tree calls the thing
  2. the facts that are easy to get wrong
  3. what it requires for safe usage

Everything about a subject is then in one place for whoever reads the guide.
It is also in front of one builder at once, which says each fact once.

Parts named for the kind of statement ("What this tree calls things", "Facts
that are easy to get wrong", "Using it safely") spread one subject over three
or four places. A different call answers each, and none can see the others.
The first guides built that way stated the same fact three times.

- Merge two questions that turn out to ask the same thing once they sit next
  to each other.
- Ask for a list only when completeness is the point, as with the variants to
  choose among, or an enumeration. Otherwise ask for the rule and where to
  find the sites.

### 7. Build

Build with every reader named. The command is under "Building". Check the
report:

- every question is answered
- what the check corrected
- what the read of the whole guide changed

### 8. Read the built guide as a person would

- Every answer should be a list that someone could check against the source
  one line at a time.
- Spot-check facts that are new to you.
- If something is missing, a question is not being asked. Add the question
  and rebuild. Never edit the built text.

### 9. Put the results in git

| Goes in | Stays out |
|---|---|
| the built guide, `kernel/subsystem/build/linus/<guide>.md` | the run report |
| its kept answers, under `answers/<guide>/` | anything that names a model |
| the measurement set | anything that gives the cost of a run |
| the results file | |
| the build set | |

Nothing else from a run goes in. This repository is public, and a run report
names the models that did the work and what the run cost. So the report stays
out, and no file in the repository names a model or gives a cost. The readers
are "reader A", "reader B" and "reader C".

- Before you commit, search what you are adding for model names.
- Delete a hand-written guide in the same commit as the built guide that
  replaces it.

### Doing several at once

Each guide is independent, so guides can be converted in parallel, with one
agent per guide. `kernel/docs/convert-guide-agent.md` is the instruction sheet
for each agent. Fill in these, and hand it over:

- the guide name
- an id prefix
- whether its hand-written guide was verified
- the model names

Eight at a time has worked on a large machine. There are two limits:

| Limit | Why | What to do |
|---|---|---|
| memory | every builder and checker process opens the semcode index | run fewer at once |
| disk | each run unpacks its own copy of the tree, nearly 2 GB, under the temporary directory. Three measurement runs and a build per guide filled it and killed a build | unpack the tree once, somewhere with room, and have every run share it with `--snapshot <dir>` |

- **The driver's own `make_snapshot()` makes a snapshot.** It runs `git
  archive` of the revision and removes any agent configuration files.
- **Put the snapshot outside your home directory.** The driver denies the
  model your whole home, and it cannot do that when the tree is in there. It
  says so in a warning that is easy to miss in a parallel run.
- **Remove stale `build-guides-*` directories** from the temporary directory.
  A run that is killed leaves its copy behind.
- **The agents write only the files of their own guide**, and they do not
  commit.
- **One orchestrator** runs `check-built-guide.py` on each guide as its agent
  reports, commits it signed off, and starts the next.

## Rebuilding

Converting a guide is done once. Rebuilding is one command:

```
kernel/scripts/rebuild-guides.sh --tree <linux> --all            # every guide
kernel/scripts/rebuild-guides.sh --tree <linux> <guide> ...      # the guides named
```

The guides go into the build directory, `kernel/subsystem/build/linus/`. It
holds the guides of one kernel: the most recent tree of Linus's that was
scanned. `kernel-version.yaml` in it records the release, as the `Makefile` of
the tree gives it, and the commit.

`--dir` builds into another build directory beside it, such as
`kernel/subsystem/build/v6.18.y/` for a stable series. A review chooses among
the build directories by the release of the tree under review, as
`kernel/subsystem/subsystem.md` says.

| You want | Run | Result |
|---|---|---|
| the guides for a newer kernel | `--all` on that tree | every guide in the build directory is replaced, and the guides of the earlier kernel are removed |
| one guide again, after its question changed | the guide's name, on a tree at the release that `kernel-version.yaml` records | the guide is replaced in the build directory |
| one guide again, on a tree at another release | the guide's name | refused: the directory would hold two releases. Use `--all` |
| one guide, when the build directory is empty | the guide's name | refused: the build directory holds every guide. Use `--all` |

The script does this:

1. It unpacks the tree once, into a scratch directory outside your home.
2. It builds each guide named, with one builder, several at a time
   (`--jobs`).
3. It runs `kernel/scripts/check-built-guide.py` on each.
4. It installs the guides that pass, all at the end.
5. It makes `subsystem-guide-index.txt` in the build directory again with
   `kernel/scripts/make-guide-index.py`, since the index holds the line number
   of every answer.

| The guide | What happens |
|---|---|
| passes | it is copied into the build directory with its answers, and the kernel is recorded in `kernel-version.yaml` |
| fails the check | it stays in the scratch directory beside its run report, for a person to read |
| has a stage that did not run | it stays in the scratch directory, with `incomplete.txt` |

`--no-build --scratch <dir>` installs what an earlier run finished.

`kernel/scripts/make-guide-index.py --tree <linux> --check` fails if the index
is not the one that the guides and the tree give. Run it before you commit a
guide.

### Which models

This repository is public and does not say. The script reads them from
`~/.config/review-prompts/build.env`, or from the file that
`$REVIEW_PROMPTS_CONFIG` names.

| Variable | What it sets |
|---|---|
| `REVIEW_PROMPTS_BUILDER` | the builder |
| `REVIEW_PROMPTS_READERS` | the readers |
| `REVIEW_PROMPTS_CHECKER` | optional. A different model for the checks (`--check-model`) |

One builder is the design. A checker that is not the builder is the way to
get an independent check.

### What the check does

`check-built-guide.py [guide ...]` looks at the guides in the build directory,
`kernel/subsystem/build/linus/`. `--dir` names another directory,
which is how a rebuild checks a guide before it installs the guide. The check
confirms that:

- the build set passes the lint
- every question asked has a kept answer
- rendering the kept answers gives the guide exactly, so nobody edited it by
  hand
- the kernel is recorded
- nothing in the guide, its answers or its question files names a model, a
  cost or a local path

**The scan for model names is always on.** Patterns are built in for the
vendor and product names, for a family name with a version, and for the shape
of a model identifier. The check also reads the names of the models actually
used from two local files. So it refuses the name of whatever model built a
guide, and this repository never has to list that name:

- that same `build.env`
- `~/.config/review-prompts/models-seen`, to which `build-guides.py` adds
  every model it is told to use. A build started by hand is covered too.

The check reports where a hit is, never what it was.

A check that passes is not a guide that is right. Read a new guide before you
commit it.

### Answers are kept

A build writes the final answers of each guide to
`kernel/subsystem/build/linus/answers/<guide>/<id>.md`. Each file holds the
text exactly
as it went into the guide, and nothing about the run.

`build-guides.py --render-only <answers dir> --out <dir>` renders the guides
from them with no tree and no model. So a change to the renderer, or to a
verbatim file, never needs a rebuild.

### One command for every guide

The header of a question file may say `- min-relevance: 3`, as the header of
`mm-folio` does, where a guide is built from fewer than all its questions. So
no guide needs a flag of its own.

### The self-test

`build-guides.py --selftest` exercises everything that needs no model:

- the parser, and which paths and ids it refuses
- selection, grouping and rendering
- answer markers
- the kernel record and render-only
- a call that stalls, and a call that keeps working

## What people do

- Write and review the questions.
- After a build, read the report.
- Diff two built guides to see what changed between two trees.

## What was tried

Each part of the build has a reason, and most of the reasons are things that
went wrong. This section records them, so that nobody tries them again.

### Word budgets

Word budgets went wrong every way they were used.

| How the budget was used | What went wrong |
|---|---|
| the first build sets were each held to the word count of the hand-written guide they replaced | questions were cut although they mattered and the readers got them wrong. BPF lost every question about maps |
| the budget of every answer was squeezed to make the sum fit | answers came out crushed, with clipped bullets and shortened names |
| budgets were made generous and called ceilings | the builder read them as the assignment, and answers filled them whatever the prompt said |
| the driver split a group into several calls once its budgets passed a total | questions about one subject were separated, and the guide said the same thing three times |

So no number says how long anything is.

### The builder copied the longest draft

With no limit on length, the builder wrote about 25,000 words for a guide that
had been 7,500. Four things were tried: an allowance for losing some content,
a rule against lists that a search would produce, reworded questions, and a
headline telling the builder not to reproduce the source. Each changed what it
wrote. None changed how much.

The cause was an input that nobody was watching. The builder was shown the
draft of each reader "so as to spend its words where they were wrong". Across
64 questions:

- the length of its answer correlated 0.84 with the length of the longest
  draft
- its answer ran 1.2 times that draft
- 58 percent of the names it quoted were already quoted in a draft

It was taking the most detailed draft as an outline, verifying each line, and
keeping the line whether the reader had been right or wrong.

**When a guide comes out long, look at what the builder was shown, not only
at what it was told.**

Three changes followed, on one section used as the test:

| Change | Result |
|---|---|
| the builder was told only to write the difference | it swapped what the readers knew for deeper material they had not raised. The size did not change |
| the difference was measured against the question | a third shorter |
| the builder had to write the list of differences first | 1,661 words became 506, with nothing for the section check to correct |

### Shortening

For a time a last stage shortened the guide once it was accurate.

1. An editor rewrote each section in fewer words.
2. A grader read the original and the rewrite side by side, and scored the
   information lost from 0 to 100.
3. A rewrite was accepted at 10 or under.
4. The same pair then went over the whole guide for what was said in more
   than one section.

It took about a fifth off a guide.

It was removed because it damaged text that had been verified, and its check
did not catch the damage. Over 650 sections the grader accepted a rewrite for
every one, and scored 468 of them 0.

Sixteen wrong statements were found by reading the built guides against the
tree. The editor had made four of them, after every check had passed:

| What the editor did | Example |
|---|---|
| closed an open list | "x sets it, and y too" became "set by x and y" |
| dropped a narrowing word | "translation never calls it" became "never called" |
| merged two bullets | the file of one function was said of both |
| took out a word | the word was one that the read of the whole guide had added to correct a statement |

Made to write its comparison out bullet by bullet, the grader caught two of
the four. With both versions quoted in its own notes, it still judged the
other two the same.

Deleting a whole bullet caused none of the four. Rewording and merging caused
three, and taking one word out caused the fourth. So one kind of deletion
remains. The section check does it, since it has the rest of the guide beside
it: what a section covers is deleted from "Model gaps", whole bullets at a
time, with nothing reworded.

A guide is a fifth longer than it was with the stage. Every statement in it
is one that a checker read against the tree, in the words it is published in.

### "Model gaps" was left alone

At first the pass over the whole guide was told to leave "Model gaps" alone.
Four fifths of the mistakes in the part were already in the sections, and that
was seven percent of every guide. Now the section check deletes from the part
whatever a section already says.

### Where wrong statements came from

Before the guides were first published, every one was read through against
the tree (`kernel/docs/read-built-guides-agent.md`). Of several thousand
statements checked, sixteen were wrong. Each was traced back through its
build.

| How many | Where it came from | What changed |
|---|---|---|
| ten | wrong in the builder's first draft, and passed two section checks and the read of the whole guide | the checker writes one record per claim, and is told what each kind of claim needs |
| two | written by a section check as a correction: it removed something wrong and put a broader claim in its place | a correction is held to the standard of the text it corrects |
| four | made by the stage that shortened the guide | that stage is gone |

- **In each of the ten, the bullet held several claims and the check had
  covered one.** The checker's note for "every ioctl flagged 0, including ...
  and all the KMS GET ioctls" shows it looking up three ioctls by name. The
  checker had been told that one record per bullet was enough.
- **One of the ten rested on a comment.**
- **In two of the ten, the convention for absent names carried the wrong
  meaning.** "No alloc_memory_type() call" was meant as "this driver does not
  call it" and reads as "it does not exist". A name copied from a reader's
  draft was put in backticks without a search for it. Plain text is now only
  for a name defined nowhere in the tree, and an absence is checked by
  searching for it.

The questions behind the sixteen are no different from the rest in length or
in how many things they ask. Six of them did have a fault of their own, and
were rewritten. "Writing a good question" now warns against the three kinds of
fault: the answer in the question, a question about comments, and a question
about the form of the answer.

### Rules that were too broad

Every `**Unsafe usage**:` statement in the built guides, 686 of them, was then
checked the other way round. A verifier searched the tree for code that does
what the statement calls unsafe.

- Two statements were wrong.
- One in five was too broad. It was true in one case, and nothing said which
  case, so correct code in the tree matched it.

| The rule called unsafe | What the tree does |
|---|---|
| `if (pm_runtime_get_if_active(dev))` followed by a put | most callers of the function do this |
| `depends on !FOO` for a symbol that only some architectures define | correct code does this |

A reviewer is told not to reason such a statement away, so each one causes a
false report when a patch matches it.

That is why a rule has two labels, and why the builder and the checker search
for contradicting code before a rule is written. See "Rules and their labels".
The verifiers also found some thirty places where the tree does what a guide
correctly calls unsafe.

### What reading the rebuilt guides found

After each rebuild of every guide, a fresh sample, chosen at random, was read
against the tree by verifiers who could not see the notes of the build.

| | First rebuild | Second | Third |
|---|---|---|---|
| Sections read, every claim | 8 | 8 | 8 |
| Claims checked, about | 660 | 850 | 670 |
| Wrong | 2 | 1 | 1 |
| Too broad | 8 | 3 | 2 |
| Rules checked | 58 | 60 | 61 |
| Rules that held | 51 | 53 | 50 |
| Deletions of repeated facts checked | | 60 | 60 |
| Deletions that lost part of a fact | | 6 | 3 |

Before the first rebuild, four rules in five held. The two claims that were
wrong after the first rebuild both came from one mistake.

**After the first rebuild**, three things were behind what failed. The
builder and the checker are now told each.

- **A claim that something is not done is about the callees too.** "Attaching
  takes no reference for the tree" was written, and twice checked, from the
  body of the function that attaches a node. The last helper it calls takes
  the reference, and that helper is an empty stub without sysfs.
- **A usage given as safe is safe under a condition of its own.** Cancelling
  work from the `close` of a device was given as safe because unregistering
  calls `close`. It does not for a device that is inhibited. The label was
  designed to stop a bug being given as good code, and no example was one. The
  two that failed were good code with the condition left off.
- **The test that the rule states has to tell its two cases apart.** In one
  rule both bullets were true, and the function given as safe fitted the
  words of the unsafe bullet.

**After the second rebuild**, every usage given as safe was safe, and the two
cases of every rule could be told apart. The seven rules that failed were all
too broad. Code that the search had not reached contradicted each one. In one,
a branch takes the safe path when its test gives the wrong answer. In another,
memory has another state that is as safe as the two the rule names. Two more
things were found, and the builder and the checker are now told both:

- **A bullet is deleted one claim at a time.** None of the sixty deletions
  lost its fact outright. Six lost part of it. In each, the bullet had held
  more than one claim, and the answer that kept the fact had only some of
  them. What went was usually the consequence. One guide kept which lock a
  domain picks, and lost that its callbacks therefore run atomic.
- **A plain name is read as absent, however well known the name is.** Names
  that every kernel developer knows were written without backticks. So was the
  name of a function, in a sentence saying there is no cleanup wrapper for it.
  The convention has no way to say "exists, but not as this", so the sentence
  has to say it.

**After the third rebuild**, four more:

- **The result of a call chain is decided by the last test in it.** "A guest
  access to an unknown register passes" was written from the first function
  in the chain, which skips a test. The function it calls makes the same
  test.
- **Notes from the last section check were lost.** The last check can only
  change its own group. What it said about an answer elsewhere went nowhere.
  It now goes to the read of the whole guide.
- **A likely bug was stated as a fact.** One guide said that a scheduler
  calls its depth callback before it sets the value that the callback reads.
  It is true, and it looks like a bug. Such code is now written as a rule for
  the pattern, or left out.
- **The searches were by name.** Rules that proved too broad had been searched
  by the name of one helper. The checker now has to record the effect it
  searched for.

**About seven rules in eight hold**, and that share has not moved over three
rebuilds. The builder searches for code that contradicts each rule, and the
section check searches again. Each search is one model's, made once, and these
rules are what it misses. The rules that fail are those where correct code
does the usage and is safe for a reason of its own.

**A rule can come and go between builds** with no change to the kernel, the
question or the prompts. The readers answer from memory, and their answers
vary from one run to the next. When every reader happens to know a rule, the
builder does not write it. This is accepted: a guide holds differences only.

After the first rebuild the verifiers also found some twenty places where the
tree does what a correct rule calls unsafe, and nothing showed the code safe.
Two of them were reached by two verifiers working from different rules. Later
samples found more. None of these places is in any guide.

### Prompts that were hard to read

The five prompts that build a guide were added to piece by piece, and became
hard to follow: invented terms, figures of speech, stacked negatives, and
rules with several cases written as one sentence. They were rewritten in plain
language, and every instruction was compared with the old text. See
`kernel/docs/writing-style.md`.

### Instructions don't belong in a guide

A built guide says how the tree is. It never tells a reviewer what to report
or not to report, so an instruction of that kind cannot live in one. The
build guide showed it.

| The build guide | What every review loaded |
|---|---|
| hand-written | 250 words of baseline: GNU C11, unsigned `char`, no strict aliasing, Python 3 |
| built | 4,200 words on Kbuild, with the baseline reduced to a list of flags |

The baseline is now written by hand in `kernel/technical-patterns.md`, under
"Language and Toolchain Baseline". `build.md` loads from its row in the table
of `subsystem.md`.

If another always-loaded file is ever converted, first separate what is
instruction from what is knowledge of the tree.

## Where things stand

- **Every subsystem guide has been converted.** All 68 have a measurement
  set, a results file and a build set, and a guide built from them, committed
  under `kernel/subsystem/build/linus/`.
- **The built guides are what a review loads.** They replaced the hand-written
  ones once every guide had been rebuilt to hold differences only, and had
  been read through. The hand-written guides, and the template they followed,
  are in the history of this repository.
- **`races.md` is the one guide with no questions.** It is the race-tracing
  method, split out of the hand-written locking guide. It is kept by hand in
  `kernel/subsystem/verbatim/races.md` and copied in.
- **`subsystem.md`, `subjective-review.md` and `README.md`** in
  `kernel/subsystem/` are not subsystem guides and have no questions.
- **`mm-folio` is built from its questions at relevance 3 and up.**
- **When a review misses a bug for want of knowledge**,
  `kernel/agent/failed-review.md` adds or sharpens a question. It never edits
  a guide.
- **For the readers of a guide and what they got wrong**, and for where its
  hand-written guide turned out to be stale, read its
  `catalogue/<guide>-measurement-results.md`.
- **`catalogue/mm-vma-measurement-116.md`** is an archive from before titles
  had a rule. It fails the lint on titles only.

`mm-vma`, `mm-folio`, `bpf`, `btf` and `libbpf` were converted by hand, which
is how the procedure was worked out. Agents that followed the procedure
converted the other 58, eight at a time, in about seven and a half hours.

One thing is left to decide: whether the second section check earns its keep,
since it twice reverted a correction that the first had made.
