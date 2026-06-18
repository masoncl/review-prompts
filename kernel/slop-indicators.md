# AI "slop" indicators

**Risk**: None. Subjective code/prose quality. Slop findings are opinions, never bugs.

**When to check**: this is the concrete arm of subjective review (`subsystem/subjective-review.md`).
It runs from `agent/review.md`'s subjective slop pass (PHASE 4.5). `agent/report.md` drops any
slop finding if the patch has a confirmed correctness regression, so slop only reaches the list
when the patch is otherwise clean. Never raise slop as part of the regression analysis itself.

This guide lists the stylistic tells that frequently appear in machine-generated or
lightly-reviewed kernel patches. The goal is NOT to label a patch as AI-written. The goal
is to spot specific, concrete spots where the code or changelog reads as unidiomatic,
verbose, or careless, and to ask the author a polite question so they can tidy it up before
human reviewers do.

## What this is NOT

- Not a bug hunt. If a finding is about correctness, it belongs in the regression pass, not
  here. Defer all correctness questions to the regression analysis. If you catch yourself
  reasoning about whether the code is correct — a race, lock ordering, a missing balance, an
  overflow — stop: that is the regression pass's job, not slop.
- Not an authorship verdict. Presence of a tell is not proof a tool wrote the code, and
  absence is not proof a human did. Never write "this looks AI-generated", never mention the
  author, never mention any tool. Talk only about the specific code or prose.
- Not an attribution check. Disclosure trailers (`Assisted-by:`, `Co-developed-by:`) are
  normalized provenance metadata, not slop — never comment on them.
- Not a style-guide sweep. checkpatch already covers mechanical formatting. Only raise things
  a checkpatch run would miss and a careful human reviewer would actually comment on.

## Confidence model (high bar)

Slop is hard to detect and easy to get wrong, and the mailing list reacts badly to low-signal
automated nitpicking. Bias heavily toward staying silent.

- **Cluster requirement.** A single weak signal is never enough. Only raise a finding when you
  have a clearly-located, concrete instance, ideally with corroboration (the same tell
  repeated, or two different tells in the same change). One redundant comment, one slightly
  long name, one extra blank line: stay silent.
- **Compare to the neighbours, not to an ideal.** The kernel is full of long, dense, and
  complex code. Judge a change against the surrounding code in the same file/subsystem. If the
  pattern matches what is already there, or there is a plausible reason for it, suppress. Pull
  the surrounding code with the code-navigation tools the review already has (semcode
  `find_function` / `grep_functions`, else grep/read on the tree) — do not guess at the
  neighbours.
- **Plausible-reason test.** Before raising anything, ask: is there a sane engineering reason a
  competent kernel developer would have written it this way? If yes, suppress.
- **Hard cap.** At most 3 slop questions for a patch. Pick the most concrete and least
  arguable. Volume is itself the problem we are trying to avoid.

## Indicators

For each indicator: the signal, how to confirm it against nearby code, the kernel norm behind
it, and an example of the kind of question to pose. Phrase every finding as a question about
the specific code, varying the wording (see `inline-template.md`).

### SLOP-COMMENT: comments that restate the code
- Signal: a comment that paraphrases the very next line, narrates unrelated subsystem internals
  (e.g. justifying a libbpf change by citing `seq_file`/`seq_path` buffer behaviour the reader
  does not need), or explains the obvious. Block comments not matching the surrounding style.
- Confirm: read the comment and the code it sits above. If removing the comment loses no
  information a kernel developer wouldn't already have, it is a candidate. Compare comment
  density to the rest of the function/file.
- Norm: coding-style — comments explain WHY, not WHAT; avoid over-commenting.
- Question: "Does this comment add anything over the code below it, or could it be dropped?"

### SLOP-VERBOSE: verbose / deeply-nested code that reads as machine-written
- Signal: the same long dereference chain (`a->b->c->d`) repeated several times instead of a
  local; indentation deeper than the surrounding code without need; gratuitous wrapper/alias
  layers.
- Confirm: count the repeats; check whether a local variable or early `return`/`goto` would
  flatten it, and whether nearby code already does so.
- Norm: coding-style — shallow indentation, readable locals over repeated derefs.
- Question: "Could `x->y->z->w` be hoisted into a local here to make this easier to read?"

### SLOP-COPYPASTE: duplicated logic instead of factoring
- Signal: a block that is a near-verbatim copy of an existing function/block; a "no functional
  change" refactor that copy-pastes a chunk under a new label instead of sharing it.
- Confirm: locate the original via grep/semcode and diff the two by eye. Confirm they are
  substantially the same logic, not coincidentally similar.
- Norm: submitting-patches — avoid gratuitous duplication; factor shared logic.
- Question: "This looks close to <existing>() — could the two share a helper?"

### SLOP-DEFENSIVE: redundant guards (style angle only)
- Signal: a NULL/bounds/overflow check added where the surrounding contract already guarantees
  the condition cannot occur, read purely as clutter.
- Confirm: only raise as slop if the redundancy is obvious from local context. If reachability
  is genuinely in question, that is a correctness matter — leave it to the regression pass and
  do not raise it here.
- Norm: coding-style — do not add unreachable/defensive checks without a real trigger.
- Question: "Is this check reachable, or is the value already constrained by the caller?"

### SLOP-DEADCODE: additions with no consumer
- Signal: a new enum value, BTF id, label, local, or helper that nothing references; a guard
  that is always false.
- Confirm: grep for the new symbol; if it has no user in the series, it is a candidate.
- Norm: coding-style — no dead code or unused symbols; build clean.
- Question: "Is `<symbol>` used anywhere in the series, or is it left over?"

### SLOP-CHURN: cosmetic edits with no behavioural reason
- Signal: reformatting, renaming, or moving code with no functional justification, especially
  folded into an otherwise focused change.
- Confirm: check the commit message for a stated reason; if the motion is unexplained and
  unrelated to the patch's purpose, it is a candidate.
- Norm: submitting-patches — separate logical changes; no churn-only edits in a feature patch.
- Question: "Is this rename/move needed for the change, or could it be split out?"

### SLOP-OVERENG: heavy machinery for a small problem
- Signal: a large new mechanism, abstraction, or reinvented standard helper (open-coding what
  a builtin or existing kernel facility already provides) for a narrow use case.
- Confirm: identify the existing facility it duplicates; weigh the added lines against the
  problem size.
- Norm: submitting-patches — smallest change that solves the problem; reuse existing infra.
- Question: "Is the existing <facility> usable here instead of this new mechanism?"

### SLOP-NAMING: identifiers that fight kernel convention
- Signal: overlong descriptive identifiers where a terse local is the norm; opaque numeric or
  encoded test names; vendor/marketing names instead of accurate kernel terms.
- Confirm: compare against naming of nearby identifiers of the same kind.
- Not slop: width/size literals the language forces (e.g. `%15s` / `%4095[^\n]` in scanf/printf
  format strings, which cannot interpolate a macro), and any literal that already matches the
  file's dominant idiom. Do not spend effort on these.
- Norm: coding-style — clear, concise, conventional names; terse locals, descriptive globals.
- Question: "Would a shorter name like `<suggestion>` read better alongside the nearby code?"

### SLOP-MSG: changelog that explains the what, not the why
- Signal: a commit message that narrates the diff line-by-line, pads length while omitting the
  load-bearing rationale, or uses a non-kernel changelog format (e.g. a `Test Plan:` block).
- Confirm: read the whole message; check whether a reviewer learns *why* the change is needed
  and how the tricky part works, or only *what* lines changed.
- Norm: submitting-patches — describe the problem and the why; imperative mood; concise.
- Question: quote the specific portion and ask, e.g. "Could the changelog say why this is
  needed rather than restating the diff?" (use `inline-template.md`'s Commit Message Issues
  format).

## Output marking

Every slop finding is a subjective observation. Emit it with:
- `issue_category: "slop"`
- `slop_indicator: "<SLOP-...>"`
- `issue_severity: "low"`
- `issue_type: "subjective"`

`report.md` and `inline-template.md` render these like SR-* subjective findings: gentle,
question-posed, "this isn't a bug, but ...", no author mention, no ALL CAPS, naming the exact
code or prose.
