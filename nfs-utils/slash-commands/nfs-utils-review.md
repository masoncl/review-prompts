---
name: nfs-utils-review
description: Review nfs-utils commits for regressions
---

Using the prompt {{REVIEW_DIR}}/review-core.md, run a deep dive regression
analysis of the specified commit, range, or patch file.

If nothing is specified, analyse the top commit (HEAD).

Load {{REVIEW_DIR}}/technical-patterns.md first, then follow the complete
review protocol in review-core.md.

For the change being analysed:

1. Understand what it is trying to do.
2. Identify every changed file and function, and classify each file: daemon,
   one-shot CLI tool, upcall handler, shared library under support/, or
   generated code.
3. Read {{REVIEW_DIR}}/subsystem/subsystem.md and load **every** matching
   subsystem guide, not just the most specific one.
4. Analyse per the protocol: error propagation, resource pairing, buffer
   sizing, control flow, privilege and ordering, conditional-build
   correctness, then caller and format compatibility.
5. Check every candidate finding against
   {{REVIEW_DIR}}/false-positive-guide.md before reporting it.
6. If findings survive, write review-inline.txt using
   {{REVIEW_DIR}}/inline-template.md.

Pay particular attention to the things this tree's build does not catch:

- `switch` over `sa_family_t` or any non-enum with a missing `break` —
  `-Wimplicit-fallthrough` is not enabled.
- A new `xlog_err()` on a path that handles a remote request; it calls
  `exit(1)`.
- An early return added between `daemon_init()` and `daemon_ready()`.
- A cross-component reference that only links in the default configuration.
- A direct `stat`/`open`/`realpath` where an `nfsd_path_*` wrapper exists.

If nothing survives verification, say so and state what you checked. Do not
pad the review with style or LOW findings.
