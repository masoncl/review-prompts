# Kernel patch review prompts

These prompts give AI extra context to more effectively review
kernel code.  They can be paired with semcode, which makes the review
sessions faster and more accurate by indexing the kernel tree, reducing the
time AI spends grepping for function/type definitions, and call graphs.

The [semcode github repository](https://github.com/facebookexperimental/semcode)
has instructions on setting up the indexing and MCP server, but if you're just
getting started, you can do the quick start without semcode.

## Quick start

Put these prompts somewhere, and then tell claude to use them:

```
claude> Using the prompt ../review-prompts/review-core.md run a deep dive regression analysis of the top commit
```

Claude has a internal definition of what "reviewing" code means, so if we call
it a review, it will generally follow that internal definition.  We can nudge it
slightly, but calling it a deep dive regression analysis leads to better
compliance with the prompts.

You can also feed it incremental diffs, or use debugging.md with an oops
or stack trace.

If you want to use this in GitHub workflows, see [this document](./docs/github-actions-claude-integration.md)
for integration instructions.

## Output

Claude will chat its way through the code review, and that output is
pretty useful.  If regressions are found, it creates a review-inline.txt
file, which is meant to look like an email that would be sent to lkml.

sample.txt has examples of regressions.

## False positives

Many of the false positives are just AI not understanding the kernel,
which is why there are per-subsystem context files.  We'll never get down
to zero false positives, but the goal is to build up enough knowledge that
AI tools can lead us in the right direction.

The false positive rate is improving, currently at ~20-30%.

## Prompt structure

review-core.md sets the checklist and also tells AI which prompts to
conditionally load.  Start reading there.

## Using agents to review the reviews

The easiest way to understand a given regression is often to load the
regression report into an AI agent and ask questions.  The agents are
generally accurate at finding details in the kernel tree, so if it claims
there is a use-after-free, ask for the call chains or what conditions it might
happen.  These really help nail things down.

## Writing new prompts

The existing prompts catch a wide variety of bugs, and most subsystems won't
need special instructions.  If you're finding false positives or missed bugs,
it can help to add a few notes to help AI get the review right.
patterns/BLOCK-001.md and patterns/LIBBPF-001.md are two examples where we fill
in extra details that you can use as a guide.

The basic structure of the prompts continues to change, and should decrease in
complexity now that we have a good baseline.  But subsystem specific prompts
usually just add a few specific details, and can be very short.

### Structure of existing prompts

technical-patterns.md includes most individual patterns, and
review-core.md includes subsystem specific prompts.  This lets us
limit tokens spent to only the prompts that are relevant to the patch.

Beyond that, the existing prompts are structured to try and make sure
AI actually follows the steps.  The basic idea:

- Explain when to run this prompt
- Add additional knowledge about code or data structures
- Put a series of steps into a TodoWrite
- Gather context needed to review the code
- Make AI produce output at each step to prove it is following instructions

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

The prompts have been developed against claude, but gemini also works well.
These should be generic enough that other agents work too, but please send patches
if we can improve performance with any of the other agents.

