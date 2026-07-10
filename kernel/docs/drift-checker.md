# Citation drift checker

The arm64 and KVM subsystem guides under `kernel/subsystem/` cite kernel
paths, symbols, and commits. The kernel moves, so a citation that was
accurate when written rots: a function is renamed, a file moves, a symbol is
removed. `kernel/scripts/check-drift.py` verifies the mechanically checkable
citations in a guide against a local kernel tree and reports each stale one,
so the guides can be kept current without a maintainer re-reading every
reference by hand.

The checker is stdlib-only Python 3 and reaches the kernel tree through git
plumbing (`git cat-file`, `git grep`, `git log`) only, so it runs wherever
git and Python are available and never modifies the tree. Every query takes a
revision (`--rev`, default the tree's `HEAD`), so a guide can be checked
against any release, and `--stats` prints the per-class checked, skipped, and
ignored counts.

Diagnostics are one line each, `<guide>:<line>: <check>: <message>`. A broken
citation exits non-zero; an age warning does not.

## Checks

- **C1, path.** A backticked path is resolved in order: exact path, then
  directory (trailing slash), then unique suffix match for a bare filename or
  a trailing fragment such as `nvhe/memory.h`. Zero matches, or a fragment
  that matches more than one file, is a finding. A guide-internal reference
  (`see kvm-arm64.md`) is resolved against this repository, not the kernel.
- **C2, symbol.** A backticked identifier is looked up in the kernel source
  with `Documentation/` excluded (see Symbol corpus). Reported when it exists
  nowhere in code. Identifiers inside fenced examples are extracted and
  existence-checked the same way, since even a deliberately-wrong example line
  uses real symbol names.
- **C3, commit.** A hex string of twelve or more digits is checked to resolve
  to a commit. When the citation is the adjacent `` `<sha>` ("subject") ``
  form, the quoted subject is compared; a bare backticked subject with no SHA
  is resolved by a fixed-string substring match over `git log --grep`.
- **C4, footer.** See Verification footer.

## Citation forms

Occurrence counts across the four guides:

| Form | Occurrences | Checked |
|------|-------------|---------|
| File paths (C1) | 42 | 34 |
| Symbols, prose and fenced code (C2) | 948 | 283 |
| Commit SHAs (C3) | 2 | 2 |
| Commit-subject citations (C3b) | 4 | 4 |
| Spec references (C5) | 9 | 0 |
| Illustrative (placeholders, literals, example locals) | 42 | 0 |
| Other | 4 | 0 |

323 of 1051 citations (31%), or 187 of 507 distinct tokens (37%), are
mechanically checked. The remainder are architectural facts, illustrative
pseudo-code, and tokens too generic to verify.

## What is checked, and what is not

The bar for a check is near-zero false positives and real power. A check that
cannot fail, because its token occurs throughout the tree, adds nothing even
though it never misfires. So the checker verifies specific, kernel-namespaced
citations (functions, kernel macros and config options, types, file paths,
commit SHAs and subjects) and leaves architectural facts to prose review.

Not checked:

- **Register, field, encoding, and instruction names** (`SCTLR_EL2`,
  `HCR_EL2.RW`, `CBNZ`, `S12E1R`). These are stated from the Arm Architecture
  Reference Manual, not from the kernel tree, so a tree lookup cannot confirm
  them. A token is treated as a kernel symbol only if it is kernel-namespaced:
  it carries an underscore, or is a lowercase identifier of four or more
  characters. All-caps or mixed-case names with no underscore are taken as
  architectural or prose.
- **Placeholders and wildcards** (`<REG>_RES1`, `ICC_IAR{0,1}_EL1`,
  `fpsimd_lazy_switch_to_*`). A backticked span containing a wildcard, brace,
  or angle bracket is a pattern, not a citation.
- **Generic tokens.** A token that occurs more than 100 times in the corpus
  cannot meaningfully fail an existence check and is skipped. Every stale
  citation this checker is built to catch resolves to well under that; the
  checked symbols top out below 100 occurrences.

## Symbol corpus

Symbols are matched against the kernel source with `Documentation/` excluded.
A documentation mention must not vouch for a symbol that no longer exists in
code. `KVM_GET_SUPPORTED_CPUID2`, for example, survives only in
`Documentation/virt/kvm/review-checklist.rst`, while the code interface is
`KVM_GET_SUPPORTED_CPUID`; a whole-tree grep would wrongly report it as live.

When a symbol sits on the same line as, or in a paragraph with exactly one,
backticked path, the checker names that file in the finding. Otherwise the
lookup is tree-wide.

## Verification footer

A guide opts in to checking by carrying a footer as its last line:

```
<!-- drift-checked: rev=<commit> date=<YYYY-MM-DD> -->
```

`rev` is the kernel commit whose tree the guide's citations were last verified
against (twelve or more hex digits); `date` is when. A guide with no footer is
skipped with an informational line, so a default run over
`kernel/subsystem/*.md` stays quiet for guides that have not been onboarded,
and adoption is per guide.

For a guide that has a footer, the checker validates that `rev` resolves and
is an ancestor of `--rev`, and warns when `date` is more than 90 days old.
`--require-footer` turns a missing footer into an error for the guides named
on the command line; continuous integration uses it on the onboarded guides.
`--all` checks a guide's citations even without a footer, for the pre-onboarding
run that decides whether the guide is ready to carry one.

The footer is the only markup the checker adds inside a guide. The guides are
fed to their readers verbatim, so the footer is an HTML comment: it does not
render, and does not read as a review instruction.

## Suppressing false positives

Suppression lives in the checker, never as in-guide markup, because a guide is
delivered verbatim to its readers and an inline ignore comment would travel
with it. Most non-citations are filtered by the shape and frequency rules
above. A short explicit skip list in the script covers the residue those
rules do not catch: author shorthand for a longer symbol (`MIN_PKVM` for
`__KVM_HOST_SMCCC_FUNC_MIN_PKVM`), metavariables (`VNCR_r`), and identifiers
that appear only in worked examples (`vcpu_reset_args`, `captured_seq`).

## Mechanical checking and drift-robust prose

The two are complementary. A worked example can be written so it does not pin
to one release's contents: commit `87f4136` rewrote the `SCTLR_EL2_RES1`
example to assert no single revision's init-macro contents, which removes that
citation from the checkable surface entirely. Robust prose reduces how many
citations there are; the checker verifies the ones that remain.
