# Instruction sheet for an agent converting one guide

Give this sheet to each agent that converts a guide. An agent either turns a
hand-written subsystem guide into a built one, or makes a guide for a
subsystem that has none. Several agents work in parallel. See "Doing several
at once" in `subsystem-questions.md`.

The part above the line is for the person who hands the sheet over. The part
below the line is for the agent. Fill these in before you hand the sheet over:

| Placeholder | What to put |
|---|---|
| `@GUIDE@` | the file name of the guide, without `.md` |
| `@PREFIX@` | a short prefix for question ids |
| `@VERIFIED@` | the words that finish the sentence "Yours ..." under "What a guide is for": "is one of those" for the six `mm-*.md` guides, "is not" for any other, "does not exist" for a new guide |
| `<hand-written guide>` | its path, if there is one |
| `<builder>` | the model that builds and checks |
| `<reader-A>`, `<reader-B>`, `<reader-C>` | the models that answer the measurement questions in step 3, and that step 7 passes as `--reader-model` |
| `<snapshot>` | the path of one unpacked copy of the tree, which every run shares |
| `<this repository>`, `<linux>`, `<scratch>` | the paths on your machine |
| `<the hosts the model service needs>` | the hosts that a sandboxed shell must reach to call the model service |

- So far reader A has been the same model as the builder.
- The model names appear only in the filled-in copy, never in anything
  committed.
- The commands in steps 3 and 7 pass `--permission-mode auto`.
- Make the snapshot once, before the agents start. See "Doing several at
  once".

---

You are making ONE kernel subsystem guide that is built from questions. If a
hand-written guide exists, the built guide replaces it. The guide is `@GUIDE@`
(file `<hand-written guide>`, if there is one). Work only on that guide. Other
agents are converting other guides in the same repository at the same time, so
touch only the files that the steps below name for your guide.

| What | Where |
|---|---|
| Repository | `<this repository>` |
| Kernel tree | `<linux>`. Read-only for you |
| Scratch | `<scratch>/@GUIDE@/`. Create it |

Every `build-guides.py` run must pass `--snapshot <snapshot>`. Without it each
run unpacks its own copy of the kernel tree, nearly 2 GB, into the temporary
directory, and several agents at once will fill that directory.

## Read first

1. `kernel/docs/subsystem-questions.md`, all of it.
   - "Converting a guide" is the procedure you follow.
   - "Writing a good question" and "Question files" are the rules for what
     you write.
2. A finished example of each file you will produce:

   | File you will produce | Example |
   |---|---|
   | build set | `kernel/subsystem/questions/mm-pagetable.md` |
   | measurement set | `kernel/subsystem/questions/catalogue/bpf-measurement.md` |
   | results | `kernel/subsystem/questions/catalogue/bpf-measurement-results.md` |

   For a bigger guide, see the `mm-folio` files in the same three directories.
3. The hand-written guide `<hand-written guide>`, if there is one.

## What a guide is for

A guide does not explain the kernel code. It states the difference between
what the models that read it believe and what the tree does:

- what the models have wrong
- what the models disagree on
- what the models have never heard of

Where the models are right, the guide says nothing. The model that reads a
guide during a review already knows a good deal from some older kernel, and
has the tree open. So a guide says what that model would not find by reading
the tree.

A guide is loaded on every patch, so its length is a cost. But no number
controls the length, and nothing shortens a guide afterwards. The builder
writes the difference, and the checks in the build make the guide accurate.

What you control is which questions are asked and how they are organised. Each
question is used twice. The answers of the models to it show what the models
believe. What it asks for sets what counts as missing from those answers.

Only the six `mm-*.md` hand-written guides were ever checked against current
sources. Yours @VERIFIED@. If yours exists and is not one of those six, treat
it as a list of topics that once mattered, not as truth:

- Don't word a question so that it presupposes a fact the hand-written guide
  states.
- Expect the built guide to differ.
- Note in your results file where the hand-written guide is stale.

## Steps

### 1. Survey the code, not the guide

Survey the structures, the files and the functions in them, the state that is
passed around, the callbacks, the locks, the documentation under
`Documentation/`, and any tests that share the source. Use
`git -C <linux> grep`, `ls`, and file reads.

### 2. Write the measurement set

The file is
`kernel/subsystem/questions/catalogue/@GUIDE@-measurement.md`.

- Write at least 14 questions and at most 90. The length of the hand-written
  guide has no bearing on the number of questions.
- Cover what the subsystem is, how it is used, what a change to it must
  preserve, and where to look in the tree.
- Every id starts with `@PREFIX@.`, and the full stop is part of the prefix.

Each question has this form: `## <id>: <Title>`, then `- section:`, then
`- relevance: N - reason`, then a blank line, then the question.

| Part | Rule |
|---|---|
| the question | asks at most three things, and has at most three question marks |
| the question | never holds the answer |
| each sentence of the question | follows `kernel/docs/writing-style.md`. It holds at most two ideas, so split a sentence that asks three things. Each "it" and "they" points at one thing, so name the thing where two are possible |
| the whole file | has no commit SHAs and no "since v6.x" |
| the title | is a topic of two to five words |
| the title | never starts with What, Which, How, When, Where or Why |
| a name that a question gives after the words "Start from" | must exist in the tree |
| a question about a rule | asks "what are the requirements for X in order to assure safe usage", and never "what usage is unsafe" |

Then check the file:

- `kernel/scripts/lint-questions.py
  kernel/subsystem/questions/catalogue/@GUIDE@-measurement.md` must exit 0.
- Every name and path in backticks in your questions must exist in `<linux>`.
  Check a name with `git grep -q -w`, and a path with `git cat-file -e
  HEAD:<path>`. Fix any that do not exist.

### 3. Measure three readers

One model, `<builder>`, checks the answers of all three readers. The loop
below starts one run for each reader. The runs can go at the same time, in the
background, and each takes ten to twenty minutes.

Every Bash call that runs `build-guides.py` needs network access. Pass
`allowed_domains: [<the hosts the model service needs>]` on that call.

   ```
   cd <this repository>
   for r in A:<reader-A> B:<reader-B> C:<reader-C>; do
     kernel/scripts/build-guides.py --no-sources --check-memory --tree <linux> --snapshot <snapshot> \
       --questions kernel/subsystem/questions/catalogue --guide @GUIDE@-measurement \
       --min-relevance 0 --checks 1 --jobs 5 --model <builder> --permission-mode auto \
       --reader-model ${r#*:} --out <scratch>/@GUIDE@/know-${r%%:*} &
   done; wait
   ```

Each run must report every question answered. If a run has no answers for a
group of questions, look in `unparsed/` under the `--out` directory of that
run, and run the ids of those questions again with `--only`.

### 4. Read the three reports

Read the three `run-report.md` files: the table and, above all, the
corrections. `kernel/scripts/compare-runs.py reader-A=.../know-A
reader-B=.../know-B reader-C=.../know-C` shows them together.

Sort what the readers got wrong into three kinds:

- names and layouts that changed
- facts that would change what a review concludes about a patch
- things a reader said it did not recognise

### 5. Write the results file

The file is
`kernel/subsystem/questions/catalogue/@GUIDE@-measurement-results.md`. Give it
the same parts as
`kernel/subsystem/questions/catalogue/bpf-measurement-results.md`:

- what all readers got wrong
- what only some readers got wrong
- what the readers already knew
- where the hand-written guide is stale
- what you leave out of the build set, and why. Add this after step 6
- the numbers: the table from `compare-runs.py`, with the cost column removed

Call the readers "reader A", "reader B" and "reader C".

**This repository is public. Write no model names, no dollar costs, and no
mention of which model is which, anywhere in any file you write in the
repository.**

### 6. Write the build set

The file is `kernel/subsystem/questions/@GUIDE@.md`. If the file exists,
replace it. An existing file is in an older format, which is obsolete. Write a
header paragraph like the one in `kernel/subsystem/questions/mm-pagetable.md`.

**Which questions.** Pick from your measurement questions. Keep the id and the
text of each question you pick, except where a rule below tells you to change
it.

- Drop a question that every reader answered correctly, or cut it down so that
  it asks only where to look.
- Keep what any reader gets wrong.
- When two questions in one part ask the same thing, merge them into one
  question.
- A question never says how long its answer should be.
- Never use the length of the hand-written guide to decide how much you write.

**The order of the parts.**

| Part | What it holds |
|---|---|
| first: "Main structures" | the one question of that part in `kernel/subsystem/questions/mm-pagetable.md`, copied |
| second: "Where to look" | the questions about which files hold what |
| then one part for each subject of the guide | the questions about that subject |
| last: "Model gaps" | the one question `@PREFIX@.model-gaps`, copied from `kernel/subsystem/questions/mm-pagetable.md` with its `- drafts: all` field |

**Organise by subject, not by kind of statement.** In the part for a subject,
give every question the same `- section:` value, so that one call to the
builder answers them together. Inside that part, use this order:

1. what this tree calls the thing
2. the facts that are easy to get wrong
3. what it requires for safe usage

Don't make parts called "What this tree calls things", "Facts that are easy to
get wrong" or "Using it safely". Such parts split one subject over three
parts. A separate call to the builder answers each part, so the guide says the
same thing three times.

**The form of a question.** Ask every question in one of three forms:

| Form | Asks |
|---|---|
| requirement | what are the requirements for X in order to assure safe usage |
| contract | what a function guarantees, what it returns and which locks it takes. Where there are several variants, which variant is used in which case |
| orientation | which file holds a thing, and what this tree calls it |

- Never ask "which fields", "which options", "which callers" or "list the
  functions". The model that reads the guide has the tree open. The guide
  names what to look up, and says what the lookup will not tell that model.
- Ask for a list only when the reader needs every item. Otherwise ask for the
  rule, and for where in the tree the rule applies.

**Titles.** A title names the thing, in the words someone would search for. It
does not name the mistake, and it never repeats the name of the part that
holds it.

**Lint.** `kernel/scripts/lint-questions.py
kernel/subsystem/questions/@GUIDE@.md` must exit 0.

### 7. Build

Build with all three readers. A large guide takes about three quarters of an
hour. Add `--keep-answers <scratch>/@GUIDE@/stage/answers` and `--record
<scratch>/@GUIDE@/stage/kernel-version.yaml` to the command below, since step
8a needs what they write.

   ```
   R="--reader-model <reader-A> --reader-model <reader-B> --reader-model <reader-C>"
   kernel/scripts/build-guides.py --tree <linux> --snapshot <snapshot> --guide @GUIDE@ --min-relevance 0 --jobs 6 \
     --model <builder> --permission-mode auto $R --out <scratch>/@GUIDE@/build
   ```

### 8. Check the build

- Every question must be answered.
- Read the built guide. Every answer should be a short bulleted list or a
  table that a person could check line by line.
- Pick four or five facts in the guide that are new to you, and check each one
  against the tree.

### 8a. Run the check script


Put three things in a staging directory, `<scratch>/@GUIDE@/stage`:

| What | How |
|---|---|
| the built guide | copy it |
| its answers, `answers/@GUIDE@/` | the build wrote them, since you passed `--keep-answers <scratch>/@GUIDE@/stage/answers` |
| a `kernel-version.yaml` | the build wrote it, since you passed `--record` |

Then run
`kernel/scripts/check-built-guide.py --dir <scratch>/@GUIDE@/stage @GUIDE@`.

The script checks three things: that the kept answers render to the guide, the
kernel record, and that nothing names a model. The script does not replace
your own reading of the guide in step 8.

### 9. Copy the built guide into the repository

| From | To |
|---|---|
| `<scratch>/@GUIDE@/build/@GUIDE@.md` | `kernel/subsystem/build/linus/@GUIDE@.md` |
| its kept answers, `<scratch>/@GUIDE@/stage/answers/@GUIDE@/` | `kernel/subsystem/build/linus/answers/@GUIDE@/` |

Your guide has to be built from the kernel commit that `kernel-version.yaml`
in the build directory records. Then make the index again:
`kernel/scripts/make-guide-index.py --tree <linux>`.

Copy nothing else. The run reports name models and costs, so the run reports
stay out of the repository.

Before you finish, search the four files you created in the repository: the
measurement set, the results file, the build set and the built guide. Search
without regard to case, for each model name you were given, for its family
name, and for dollar amounts. The search must find nothing.

## Mistakes that earlier agents made

- **Don't wait for a build with a `pgrep -f` loop.**
  `until ! pgrep -f 'build-guides.py.*--guide X'; do sleep 10; done` never
  ends. `pgrep -f` matches whole command lines, and the shell that runs the
  loop has that pattern in its own command line, so the loop finds itself. A
  batch of agents left seventeen of these sleeping for hours after every
  build had finished. Do one of these instead:
  - start the builds with `&` and `wait` in the same command, as step 3 shows
  - run the command in the background, and let the harness tell you when it
    exits
  - if you must poll, poll for a file that the build writes last
    (`run-report.md`), not for a process
- **End no command with a bare `ls`.** On some machines `ls` is an alias for a
  tool that reads file names from standard input when standard input is not a
  terminal. In a background command standard input is a socket that never
  closes, so the listing blocks for ever and the task never completes. Use
  `/bin/ls`, and add `</dev/null` to any command that may read standard input.
- **Run `lint-questions.py` on the measurement file and on the build file in
  separate invocations.** The two files share ids on purpose, and one
  invocation over both reports duplicates.
- **When the built guide and something you believe disagree on a fact, settle
  it by reading the code**, not a comment above the code. Read the function
  from its first test down. Two mistakes have happened:
  - Builders have copied a return value, a threshold and an ordering from
    kerneldoc that the body below it contradicts.
  - A correction once made a guide wrong. A guide was rebuilt to say that a
    split of the huge zero folio returns -EINVAL, "not the comment's -EBUSY".
    The reason given was a branch in `folio_check_splittable()` that names the
    case. But an earlier test in the same function returns -EBUSY for that
    folio first, so the branch never runs for it, and the comment was right.

  A caller sees the result of the first test that a case matches. Before you
  call a comment wrong, check that no earlier test returns first.
- **Reread every build question for a clause that presupposes something the
  old guide says.** "How is X written when Y" assumes that X is supported. Ask
  "does the tree support X, and how", and name the code that would have to
  handle it. One builder twice answered a question that presupposed its answer
  by repeating the documentation, while the code did not do what the
  documentation described.
- **If you change a question after building, for any reason, rebuild the guide
  yourself from the final question text before you copy it in.** A built guide
  must always match the questions that are committed with it. If a build has a
  flaw that the question did not cause, leave the build as it is and describe
  the flaw in your report. The orchestrator, who gave you this sheet, then
  rebuilds.
- **In zsh, `$R` in the command of step 7 is passed as one word**, as is any
  variable that holds several options. Write the `--reader-model` options out,
  or run the commands with `bash -c`.

## Do not

- Do not `git commit`, `git add`, push or change branches. The orchestrator
  commits.
- Do not edit the hand-written guide, the scripts under `kernel/scripts/`, the
  prompts under `kernel/agent/`, `AGENTS.md` or
  `kernel/docs/subsystem-questions.md`. If you hit a bug in a script, work
  around it and say so in your report.
- Do not edit a built guide. If it is wrong, fix the question and rebuild.
- Do not write anywhere in `<linux>`.
- Do not leave `__pycache__` directories in the repository. Run
  `rm -rf kernel/scripts/__pycache__` when you are done.

## Report back

Report in under 250 words:

- the word count of the hand-written guide
- how many measurement questions and how many build questions
- how many corrections each reader needed
- the word count of the built guide
- the three or four most important things the readers got wrong
- where the hand-written guide is stale
- anything that went wrong, or that you worked around
