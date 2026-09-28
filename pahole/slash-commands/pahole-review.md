# /pahole-review - pahole Patch Review

Review the supplied patch/commit, or the top commit, for pahole regressions.

1. Load `review-core.md` and `technical-patterns.md`.
2. Classify changed code as reader/writer boundary, common type/layout model,
   DWARF, BTF, `pfunct`/`fullcircle`, CLI/output, tests, build, or the embedded
   libbpf submodule; load the matching guide.
3. Trace changed data from source debug information through the `struct cu`
   graph to its output/encoder consumer.
4. Check the patch against the review checklist and its focused regression test.
5. Report only concrete, reachable findings. Include input shape, affected path,
   and observable result, with a minimal correction where useful.

Pay special attention to CU-scoped type IDs, optional debug attributes,
bitfield/layout arithmetic, BTF ordering, cleanup after encoding failures, and
tests accidentally using an installed binary instead of the build output.
