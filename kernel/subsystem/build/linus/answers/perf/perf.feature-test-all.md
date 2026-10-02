- `test-all.bin` builds: every name in `FEATURE_TESTS` is set to 1 by
  `feature_set`, whether or not `test-all.c` includes its test.
- `FEATURE_TESTS=all` (the `feature-dump` goal): the fast path sets the
  `FEATURE_TESTS_EXTRA` names to 1 too.
- Re-tested by `tools/build/Makefile.feature` after the fast path: only the
  names under `ifeq ($(feature-all), 1)`, namely `compile-32`,
  `compile-x32`, `bionic`, `babeltrace2-ctf-writer`, `libunwind`,
  `libunwind-debug-frame` and the per-arch libunwind tests.
- Comment in `Makefile.feature` that both lists are included in
  `test-all.c`: does not match the file; compare the list with the
  `#include` lines instead.
- `fortify-source`: has no include in `test-all.c`; `BUILD_ALL` in
  `tools/build/feature/Makefile` passes `-O2 -D_FORTIFY_SOURCE=2` instead.
- Slow path: one `$(shell $(MAKE) ...)` per name inside `$(foreach ...)`.
- Link flags of `test-all.bin`: the flags written in `BUILD_ALL`, plus
  `FEATURE_CHECK_LDFLAGS-all`, which `set_test_all_flags` builds from
  `FEATURE_CHECK_LDFLAGS-<name>` of each name in `FEATURE_TESTS`.
- **Potentially unsafe usage**: a name in `FEATURE_TESTS_BASIC` whose test
  `test-all.c` does not include.
  - Unsafe: when nothing calls `feature_check` for the name before
    `Makefile.config` reads `feature-<name>`; where `test-all.bin` builds
    the value is 1 with the library absent, and the perf build fails later
    on the missing header or library.
  - Safe: test included in `test-all.c` and called from its `main()`, with
    the `-l` flag in `BUILD_ALL`, as `libzstd` is.
  - Safe: in a build without `FEATURES_DUMP=`, `Makefile.config` calls
    `$(call feature_check,<name>)` before every read, as it does for
    `libbfd` under `BUILD_NONDISTRO`.
