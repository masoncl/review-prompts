# Kernel patch review prompts

These prompts give AI extra context to more effectively review
kernel code.  They can be paired with semcode, which makes the review
sessions faster and more accurate by indexing the kernel tree, reducing the
time AI spends grepping for function/type definitions, and call graphs.

The [semcode github repository](https://github.com/facebookexperimental/semcode)
has instructions on setting up the indexing and MCP server, but if you're just
getting started, you can do the quick start without semcode.

If you use semcode to index lore archives, the review prompts will search
through lore as part of the review.

## Installation

Run the setup script from the root of this repository to
install the kernel skill and slash commands:

```bash
./setup.sh <agent> kernel
```

Where `<agent>` is one of the available agents, which are stated in the usage
message when the script is executed with `-h|--help` option.

For Claude Code this installs the files below.  Other agents get the same
files in their own directories.
- **Kernel skill** (`~/.claude/skills/kernel/SKILL.md`) - Automatically loads
  kernel-specific context when working in kernel trees
- **Slash commands** (`~/.claude/commands/`) - Quick access to common operations:
  - `/kreview` - Review a single commit for regressions
  - `/kseries` - Review an entire patch series (git range) commit-by-commit
  - `/korcreview` - Review a single commit with the work split across
    several agents, following agent/orc.md
  - `/kdebug` - Debug kernel crashes and warnings
  - `/kverify` - Verify findings against false positive patterns
  - `/kslop` - Run only the subjective pass of a review: code quality, and
    signs of machine-written code
  - `/cocci` - Generate a Coccinelle semantic patch

The skill and commands reference the prompts directory where you cloned this
repository, so don't move it after installation.

## Quick start

Put these prompts somewhere, and then tell the agent to use them:

```
> Using the prompt ../review-prompts/kernel/review-core.md run a deep dive regression analysis of the top commit
```

The agent has an internal definition of what "reviewing" code means, so if we
call it a review, it will generally follow that internal definition.  We can
nudge it slightly, but calling it a deep dive regression analysis leads to
better compliance with the prompts.

You can also feed it incremental diffs, or use debugging.md with an oops
or stack trace.

If you want to use this in GitHub workflows, see [this document](./docs/github-actions-claude-integration.md)
for integration instructions.

## Kernel patch review helper scripts
See [scripts/scripts.md](scripts/scripts.md) for description of how to run
a review of multiple commits in parallel.

## Output

The agent will chat its way through the code review, and that output is
pretty useful.  If regressions are found, it creates a review-inline.txt
file, which is meant to look like an email that would be sent to lkml.

sample.txt has examples of regressions.

## False positives

Many of the false positives are just AI not understanding the kernel,
which is why there are subsystem guides.  We'll never get down
to zero false positives, but the goal is to build up enough knowledge that
AI tools can lead us in the right direction.

The false positive rate is improving, currently at ~10%

## Prompt structure

review-core.md sets the checklist and also tells AI which prompts to
conditionally load.  Start reading there.

| Prompt | When a review reads it |
|---|---|
| technical-patterns.md | always |
| subsystem/subsystem.md | always.  It says how to find what the subsystem guides say about the patch |
| callstack.md | for a patch that is not trivial |
| lore-thread.md | when semcode has the lore archives |
| fixes-tag.md, missing-fixes-tag.md | when the review checks Fixes: tags |
| false-positive-guide.md | only after the review suspects a regression |
| inline-template.md | when it writes review-inline.txt |

## Subsystem guides

A subsystem guide lists where the kernel tree differs from what the models
believe about it: names that are gone, what a function requires, and rules
about unsafe usage.

Newer models actually understand the kernel pretty well, but they are always a
little bit out of date. A guide does not explain its subsystem, instead it
explains what the models are most likely to have wrong.

- The guides are built, not written by hand.  Each one comes from a file of
  plainly worded questions, subsystem/questions/<guide>.md, answered against
  a kernel tree and checked against it.
- The built guides are in subsystem/build/linus/.  They are built from the
  most recent tree of Linus's that was scanned, and kernel-version.yaml in
  that directory says which release and commit that was.
- subsystem/build/ can hold other builds beside linus, such as one for a
  stable series.  A review chooses the one that best suits the tree under
  review.
- A review does not load whole guides.  It searches
  subsystem-guide-index.txt in the directory it chose for the symbols the
  patch touches, and reads the answers that the search finds.
- A few guides are loaded whole, since they apply to a kind of file or a kind
  of bug: races, selftests, Kconfig, the build system and Rust.
- Three guides also hold the conventions that the maintainers of the
  subsystem ask of new code: hwmon, leds and mfd.  That text is kept by hand
  in subsystem/verbatim/, and the build inserts it.

| To learn | Read |
|---|---|
| how to read a guide, and what is in subsystem/ | subsystem/README.md |
| what a review does with the guides | subsystem/subsystem.md |
| how the guides are built and rebuilt | docs/subsystem-questions.md |

## Using agents to review the reviews

The easiest way to understand a given regression is often to load the
regression report into an AI agent and ask questions.  The agents are
generally accurate at finding details in the kernel tree, so if it claims
there is a use-after-free, ask for the call chains or what conditions it might
happen.  These really help nail things down.

## Writing new prompts

The existing prompts catch a wide variety of bugs, and most subsystems won't
need special instructions.  If you're finding false positives or missed bugs,
it can help to tell the AI what it is getting wrong about your code.
The subsystem guides do exactly that.  To add to one, you add a plainly worded
question to subsystem/questions/<guide>.md and the guide is rebuilt against a
kernel tree.  Never edit a built guide: the next build would undo the edit.
subsystem/questions/block.md and subsystem/questions/libbpf.md are small
examples, and agent/failed-review.md is the prompt that turns a missed bug
into a question.

The basic structure of the prompts continues to change, and should decrease in
complexity now that we have a good baseline.

### Structure of existing prompts

technical-patterns.md includes most individual patterns, and
review-core.md sends the review to subsystem/subsystem.md for what is
specific to a subsystem.  A review reads only the answers that its search of
the index finds, which limits tokens spent to what is relevant to the patch.

## review-stat.md

The BPF CI sends reviews based on these prompts to the BPF mailing list.
review-stat.md can be used to compile a report about how effective these
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
