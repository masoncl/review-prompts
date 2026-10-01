# /pahole-verify - pahole Patch Verification

Verify the supplied patch/commit, or the top commit.

1. Load `review-core.md`, then relevant focused guides.
2. Configure and build with CMake.
3. Run the changed test and relevant nearby tests; use the `check` target for
   shared loader/encoder changes when the environment permits.
4. Record prerequisites and distinguish skips from failures.
5. Check that emitted text and/or BTF semantics match the patch’s stated goal.

Report PASS, FAIL, or SKIP for build, focused tests, broader tests, and each
relevant semantic concern. Do not claim full BTF/DWARF coverage merely because
the code compiled.
