# Instruction sheet for an agent reorganising question files

Give this sheet to an agent that rewrites the question files under
`kernel/subsystem/questions/` into the form the builder needs. Before you give
the sheet to the agent, add the list of files and the path of the kernel tree
to it. The agent changes question files only. It runs no build and no model.

---

You are rewriting the questions in a few files under
`kernel/subsystem/questions/`. Work only on the files you are given. Other
agents are doing the other files at the same time.

## What the questions are for

A subsystem guide does not explain the kernel code. It states the difference
between what the models that read it believe and what the tree does.

A build first asks each reader model every question. The reader model answers
from memory, without the tree. Then a builder with the tree in front of it
writes, for each question, only the difference:

- what a reader has wrong, and what is true instead
- what readers disagree on
- what readers left blank
- **what the question asks for that no reader supplied**

So each question is used twice. The answers of the models to it show what the
models believe. What it asks for sets what counts as missing from those
answers.

- A question that asks for many things gets a long answer.
- A question that asks for the members of a structure gets them written out,
  even when another instruction says not to list them.

Read these first:

1. `kernel/docs/subsystem-questions.md`: the opening, "Question files" and
   "Writing a good question".
2. The worked example, `kernel/subsystem/questions/mm-pagetable.md`. The git
   history of that file holds the version from before the commit "questions:
   mm-pagetable and locking by subject". Comparing that version with the
   current one, question by question, teaches most of what this sheet says.
3. For each of your files,
   `kernel/subsystem/questions/catalogue/<guide>-measurement-results.md`. What
   the readers got wrong tells you which subjects matter most.

## What to do to each file

### Organise each file by subject, not by kind of statement

| Part | Rule |
|---|---|
| `# Main structures` | before the subjects |
| `# Where to look` | before the subjects, if the file has one |
| one part for each thing the guide is about, which this sheet calls a subject | after those two |
| `# Model gaps` | last |

- In the part for a subject, give every question a `- section:` line that
  holds the name of the part, so that one call to the builder answers them
  together.
- Inside a subject, put the questions in this order: what this tree calls the
  thing, what it guarantees, what it requires for safe usage.
- Split a subject that has more than twelve questions into two subjects.
- A file must have no parts called "What this tree calls things", "Facts that
  are easy to get wrong", "Using it safely" or "Changing the implementation".
  With such parts, several calls to the builder answer one subject, and no
  call gets the answers of another call.

### Ask every question in one of three forms

| Form | Asks |
|---|---|
| Requirement | what are the requirements for X in order to assure safe usage? |
| Contract | what does X guarantee, return and lock? Which of X, Y and Z is used when? What must a caller have done first? |
| Orientation | where is X defined, and what does this tree call X, in the cases where a reader remembers another name? |

There is no fourth form.

Never ask "which fields", "which members", "which options", "which callers",
"which architectures", "which files", "list the functions" or "give a table of
the fields". The model that reads the guide has the tree open and gets such a
list with one search.

A table in an answer is for variants that a reader has to choose among, or for
an enumeration whose values change what code must do.

### Ask two or three things in one question

Count the things a question asks for. Each gets its own paragraph in the
answer.

- If a question asks for more than three things, it is a checklist. Split it,
  or keep the two that a reviewer would act on.
- Ask what a reviewer would get wrong. Don't ask how something works inside.

### Never ask for a thing and forbid it in the same question

Don't ask about the state of a structure and then say "do not list its
members". Ask something that can be answered without the members. If you add
"but do not ..." to a question, the question is wrong.

### Merge and drop

- After you group the questions by subject, merge two questions that ask the
  same thing.
- Drop a question that asks only for a list, such as what a function skips, or
  which debug options exist.
- Exception: ask about one thing in that list if the measurement results show
  the readers badly wrong about that thing, and that thing would change a
  review.

### Keep these parts of the file

| Keep | How |
|---|---|
| the header lines `- guide:` and `- title:` | as they are |
| the overview question under `# Main structures` | keep the question, and use the wording in `mm-pagetable.md` |
| the whole `# Model gaps` part | exactly as it is, with its `- drafts: all` line |
| any question with `- verbatim:` | as it is |

Replace the paragraph of prose under the header with the paragraph in
`mm-pagetable.md`. That paragraph names two files. Change both names to the
names for your guide.

### Ids

- Keep the id of a question where its subject is unchanged.
- Give a merged question a new id that starts with the prefix the other ids in
  the file have.
- Ids are lower case, with single dots and hyphens.

### Titles

- A title is two to five words.
- It is a noun phrase that a reviewer would scan for.
- It never starts with What, Which, How, When, Where or Why.
- It has no final punctuation.
- **A title names the thing, in the words someone would search for. It does
  not describe the mistake.**
- If the answer is about a function, a structure or a flag, the plain-word
  name of that thing belongs in the title.
- A title never repeats the name of the subject it is under.
- The name of a subject also names the thing, in the words someone would
  search for.
- Put a question under the subject whose code the question is about, not under
  the subject where you found it.

| Unclear | Better | Why |
|---|---|---|
| "Zones that count" | "Zones in balance checks" | "Zones that count" tells a reader nothing until the reader has read the answer. "Zones in balance checks" tells a reader whether to read it |
| "Hopeless nodes" | "kswapd failure count" | |
| "Charging and recording one cgroup" | "Swap charge and cgroup id" | |
| "Pressure and balance", a subject | "kswapd, throttling and balance" | |

### Other details

- Keep each `- relevance: N - reason` line. Rewrite the reason if the
  question changed.
- A question file has no `- words:` line.
- Never put the answer in the question.
- Write no commit ids and no "since v6.x".
- Keep the "Start from `name`" pointers.
- Check every name you leave in backticks against the tree with a search. The
  name has to be defined there. Drop or correct a name that is not.
- Nothing in the file may name a model, a cost or a local path. Call the
  reader models "the readers" or "reader A".

## Check and record

1. `kernel/scripts/lint-questions.py kernel/subsystem/questions/<guide>.md`
   must exit 0 for each file.
2. Append a section `## Questions reorganised` to
   `kernel/subsystem/questions/catalogue/<guide>-measurement-results.md`. In
   three to eight lines, say:
   - what the subjects now are
   - which questions were merged, as old ids to new ids
   - which questions were dropped, and why
3. Do not run `build-guides.py` or any model. Do not edit anything else. Do
   not commit.

## Report back

Report on each file, in under 250 words in all:

- the number of questions before and after
- the subjects
- what was merged and what was dropped
- anything you were unsure of
