# Kernel patch review prompts

These prompts give claude code enough extra context to more effectively review
kernel code.  They are meant to be paired with semcode, which makes the review
sessions a faster and more accurate by providing function definitions and call
graphs.  semcode isn't released yet, but claude can usually find these things
pretty well, so these prompts work well enough to start discussing them.

I've been testing them in two basic ways:

Collecting Fixes: patches and running the prompts against the known bad
commits.  This lets me grade success rate, which is currently at 50% for a set
of 300 regressions fixed between 6.16 and 6.17.

Running reviews against upstream -next branches.  This tends to find
regressions in about 10% of the patches.  The false positive rate is about 20-30%%
so far.

## Basic usage

Put these prompts somewhere, and then tell claude to use them:

```
claude> Using the prompt ../review/review-core.md and the review prompt directory ../review, review the top commit
```

You can also feed it incremental diffs.

## Output

Claude will chat its way through the code review, and that output is
pretty useful.  If regressions are found, it creates a review-inline.txt
file, which is meant to look like an email that would be sent to lkml.

sample.txt has examples of regressions.

## False positives

Many of the false positives are just claude not understanding the kernel,
which is why there are per-subsystem context files.  We'll never get down
to zero false positives, but the goal is to build up enough knowledge that
AI tools can lead us in the right direction.

The false positive rate is pretty high right now, at ~50%.

Generally speaking claude sonnet is:

- Good at following code logic
- Good at spotting use-after-frees
- Good at ABBA style deadlocks, or flat out missing locks
- Fair at reference counting.  We do this in a lot of different ways and
claude tries his best.
- Bad at array bounds violations
- Really bad at race conditions

Longer explanations are more likely to be false positives.

## Prompt structure

review-core.md sets the checklist and also tells AI which prompts to
conditionally load.  Start reading there.

## Using agents to review the reviews

The easiest way to understand a given regression is often to load the
regression report into an AI agent and ask questions.  The agents are
generally accurate at finding details in the kernel tree, so if it claims
there is a use-after-free, ask for the call chains or what conditions it might
happen.  These really help nail things down.

## review-stats.md

The BPF CI sends reviews based on these prompts to the BPF mailing list.
review-stats.md can be used to compile a report about how effective these
reviews are.  The idea is to compile a list of all the message-ids from
the automated reviews, and then have AI use semcode to pull down those
threads and analyze the results one at a time.

It outputs two files, (review-analysis.txt and review-details.txt), and they
are meant to be concatenated together after the run is done.

Sample output is in examples/review-stat.txt

## Patches are welcome

Right now I'm more focused on reducing false positives than finding every bug.
We need to make sure kernel developers find the output useful and actionable,
and then we can start adding it into CI systems.

With that said, patches to firm up any of the subsystem specific details or
help it find new classes of bugs are very much appreciated.

I've been using claude, but I also welcome patches to make these more
effective with any of the AI agents.
