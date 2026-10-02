# Writing style

Follow this guide for everything you write in this repository: prompts,
questions, docs and commit messages. Write so that only one reading is
possible, since the reader cannot ask what you meant. Aim for clarity, not
for brevity.

Read this guide before you write or reword a prompt. A model follows a hard
prompt badly, and nobody notices until a guide is wrong.

## Words

| Rule | Instead of | Write |
|---|---|---|
| Use the ordinary word | "stated flatly" | "states no condition" |
| Use the ordinary word | "a list that reads as complete" | "a list that looks complete" |
| Don't invent a term | "a claim has one home" | "each claim belongs in one answer" |
| Don't invent a term | "an inventory" | "a list that one search produces" |
| Use one term for one thing | "reader model" here, "reader" there | "reader" in both places |
| Use no figure of speech | "stake a review on" | "rely on in a review" |
| Use no figure of speech | "check a rule from the other side" | "search for code that breaks the rule" |
| Don't write that code means, wants or asks | "the code means to do it" | "the behaviour is intentional" |
| Keep every word the grammar needs | "guide names lookup, not result" | "a guide names what to look up" |
| Use at most three nouns in a row | "section check note handling" | "how a section check handles a note" |

## Sentences

- **Open with the answer. Open an instruction with the action.**
  - Instead of: "A claim is checked when you have tried to prove it false and
    failed, not when you have found something that agrees with it."
  - Write: "Try to prove each claim wrong. Finding one line that agrees is
    not enough."
- **Say who does what.** Use the active voice.
  - Instead of: "The consequence is what a reader acts on."
  - Write: "A reader acts on the consequence."
- **Put at most two ideas in a sentence.**
  - Instead of: "A consequence is a claim of its own, so the truth of what it
    follows from does not make it true."
  - Write: "Prove a consequence separately. A true cause does not prove it."
- **Use at most one negative in a sentence.**
  - Instead of: "If you did not look, you do not know, and what you do not
    know does not go in the guide."
  - Write: "Only write what you confirmed in the code."
- **Make every "it", "this" and "that" point at one thing.**
  - Instead of: "It confirms the fact is there and restores it if it is not."
  - Write: "That check confirms the fact is there, and restores the fact if
    it is missing."
- **Say how two claims relate**, with a word such as so, since, yet, unless or
  instead.
  - Instead of: "The reader has the tree open. Don't copy the header."
  - Write: "The reader has the tree open, so don't copy the header."
- **Give a reason only if the reader needs the reason to decide what to do.**

## Words that say how strong an instruction is

"Never", "must", "only", "prefer" and "may" say how strong an instruction is.
Keep each one exactly as strong when you reword, since a softer or harder
word changes what a model does.

| The original says | Don't write |
|---|---|
| "never" | "don't" |
| "prefer a list" | "use a list" |
| "prefer a list" | "don't use a sentence" |
| "may fail" | "fails" |
| "for example: A, B, C" | "one of A, B, C" |

## Structure

- Put three or more steps, conditions or alternatives in a list, not in one
  sentence.
- Put a rule that has cases in a table, with the result in the last column.
  If a cell needs more than a few words, use a bulleted list instead.
- Give each rule one concrete example. In a prompt, use made-up names such as
  `x_find()`, so that the prompt holds nothing from a real guide.
- Say each thing once.
- State the claim first, then the evidence.
- When you correct something you said earlier, open with the correction.
- Separate what you established from what you infer, and say which is which.

### Turning prose into a table

A table shows only the cases its writer thought of. Check that the table
keeps three things from the prose:

- every case
- every general condition, such as "only when X"
- every word that says how strong an instruction is

For example, this sentence is hard to follow. In it a draft is what a model
answered from memory, and a difference is something to write in the guide.

> If the drafts said nothing about something the question did not ask, that
> is not a difference, however interesting and however true it is.

This table says the same thing:

| The question asks | A fact that is in no draft | Write the fact? |
|---|---|---|
| which lock `x_find()` holds | which lock it holds | Yes |
| which lock `x_find()` holds | that `x_find()` leaks on its error path | No. The question did not ask |

## Commit messages

- Subject: the area, then what changed, as in "build-guides: stop model calls
  that stall".
- Body: one short paragraph in plain words.
- Every commit carries a `Signed-off-by:` with a real name and email address.

## Changing a prompt

A prompt is an instruction to a model, so a change of wording can change what
the model does.

1. Read the prompt yourself and mark what is hard to follow. Don't use word
   counts or pattern matches to find the hard parts.
2. Ask a reader who has never seen the prompt to list every sentence that the
   reader had to read twice. A writer misses the hard parts of their own
   text.
3. Rewrite the prompt.
4. Compare the old text with the new, one instruction at a time. Look for an
   instruction that is lost, weaker, stronger or different.
5. Keep every output format the same, character for character, since
   `build-guides.py` parses each format.
6. Build one or two guides into a scratch directory, and confirm that
   `build-guides.py` can still parse what the models hand back.

Don't change a prompt while a build is running, since the build reads each
prompt file as it goes.
