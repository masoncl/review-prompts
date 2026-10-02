# Instruction sheet for an agent fixing titles and subject names

Give this sheet to an agent when the headings in built guides turn out to be
unclear. Fill in the list of files. The agent changes headings only, so every
guide can be produced again from the answers that the build kept, without a
rebuild.

---

You are fixing the headings in a few question files under
`kernel/subsystem/questions/`. The headings of a built guide come from its
question file. Work only on the files you are given. Other agents are doing
the other files.

A built guide has two levels of heading:

| In the question file | In the built guide |
|---|---|
| a `# Part`, which is a subject | a `##` section |
| the title of a question: the text after the id in `## <id>: <Title>` | the bold line above its answer |

These headings are all a reader has when the reader decides whether an answer
is worth reading.

## The rule

**A title names the thing, in the words someone would search for. It does not
describe the mistake.**

- A title is the plain-word name of what the answer is about: the function
  family, the structure, the lock, the flag or the phase.
- Someone who has not read the answer must be able to tell from the title
  what the answer is about.
- The same rule holds for the name of a subject.
- A title never repeats the name of the subject it is under.
  `kernel/scripts/lint-questions.py` reports that as an error.
- Put a question under the subject whose code the question is about.

| Unclear | What the answer is about | Better |
|---|---|---|
| Zones that count | which zones the balance checks look at | Zones in balance checks |
| Hopeless nodes | the count of failed background reclaim runs | kswapd failure count |
| Accounting in both implementations | counters kept by both LRU implementations | Counters in classic and MGLRU |
| Charging and recording one cgroup | which cgroup a swap charge and its id go to | Swap charge and cgroup id |
| Domain of a throttle control | the writeback domain behind a dirty throttle | Dirty throttle domains |
| Using a looked-up folio | what is safe after a swap cache lookup | After a swap cache lookup |

An example for a subject: "Pressure and balance" is unclear, and "kswapd,
throttling and balance" is better.

An example of a question under the wrong subject: a question about
`struct_size()` does not belong under "Files, ioctls and debugfs".

## What to do

For each of your files, open the built guide
`kernel/subsystem/build/linus/<guide>.md`
beside the question file. Go through every heading of the question file in
order.

1. **For each title**, read the first few bullets of the answer under it.
   Rename the title if the title alone does not tell a reader what the answer
   is about.
   - Most titles are fine. Expect to change about one in six, and fewer in
     some files.
   - Don't rename a title that already names what its answer is about.
2. **For each subject**, look at the titles under it. Rename the subject if its
   name does not say what those titles have in common. To rename it, change
   the `# Part` line, and change the `- section:` line of every question in
   it to the same new name.
3. **If a question is under the wrong subject**, move the whole question,
   unchanged, to the right subject. Set its `- section:` to match.
4. **Fix every title that the lint reports** because the title repeats the
   name of its subject.

## What must not change

- **No id, and no word of the text of any question.** The answers are kept by
  id, and the guides are rendered again from them.
- The header lines.
- The name of the first part, `# Main structures`, and the title of the
  question in it.
- The name of the last part, `# Model gaps`, and the title of the question in
  it.

Only these may change: titles, subject names, `- section:` lines, and where a
question sits.

A title must still follow these rules:

- two to five words
- a noun phrase
- never starts with What, Which, How, When, Where or Why
- no final punctuation
- no backticks

Nothing in the file may name a model, a cost or a local path.

## Check and report

`kernel/scripts/lint-questions.py kernel/subsystem/questions/<guide>.md` must
exit 0 for each file.

Do not run `build-guides.py` or any model. Edit only the question files you
were given. Do not commit.

Report on each file, in under 300 words in all:

- every heading you changed, as `old -> new`
- every question you moved
- how many titles you left alone
