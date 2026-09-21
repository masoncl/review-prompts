---
name: nfs-utils-verify
description: Verify nfs-utils findings against false positive patterns
---

Using the prompt {{REVIEW_DIR}}/false-positive-guide.md, verify that a
reported issue in nfs-utils is real.

This validates potential bugs found during review, by a static analyser, or by
another agent. nfs-utils has several deliberate idioms that look like bugs, so
run this before reporting anything.

For each issue:

1. Check it against the twelve documented false-positive patterns in
   false-positive-guide.md. The most common by far:
   - `xlog_err()` never returns, so code after it is unreachable and needs no
     NULL guard.
   - `xmalloc`/`xstrdup` abort on OOM, so unchecked returns are correct in
     `mount`/`exportfs`.
   - `strncpy()` followed by a forced NUL, or into a pre-zeroed buffer.
   - rpcgen output and YNL netlink headers are generated, not hand-written.
2. Trace the exact code path that reaches it. Do not infer reachability.
3. Confirm the code is actually compiled in a normal configuration — read the
   `Makefile.am`, not only the `#ifdef`s.
4. Confirm the line is added by the change under review, not pre-existing
   context. Legacy code is grandfathered.
5. Confirm the build would not already have rejected it: the tree uses a large
   `-Werror=` set (missing-prototypes, format=2, return-type, switch,
   unused-result and more). The notable gap is
   `-Wimplicit-fallthrough`, which is **not** enabled, so a missing `break` in
   a non-enum `switch` is a genuine finding.
6. State a concrete input or sequence that produces the wrong outcome. If you
   cannot, there is no finding.

Output per issue:

- **VERIFIED** — real. Give the reaching path, the concrete trigger, and the
  severity.
- **ELIMINATED** — a false positive. Name which pattern it matches and why the
  code is correct as written.
