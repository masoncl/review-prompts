- `FEATURE_TESTS_EXTRA` in `tools/build/Makefile.feature`: not part of
  `FEATURE_TESTS` in a default build; `FEATURE_TESTS` defaults to
  `FEATURE_TESTS_BASIC`, and becomes both lists only for the `feature-dump`
  goal (`tools/perf/Makefile.perf`).
- Name in `FEATURE_TESTS_EXTRA` (in a default build) or in neither list:
  `feature-<name>` is empty unless something calls
  `$(call feature_check,<name>)`, as `tools/perf/Makefile.config` does for
  `libcapstone` (in `FEATURE_TESTS_EXTRA`) and `llvm-perf` (in neither).
- `FEATURES_DUMP=<file>` builds: `Makefile.config` includes the file
  instead of `Makefile.feature`, so `feature_check` is undefined and each
  `$(call feature_check,...)` expands to nothing.
- `FEATURE-DUMP` contents: only the names in `$(FEATURE_TESTS)`; a name in
  neither list is absent from it and reads as off in a `FEATURES_DUMP=`
  build, which is how the `build-test` target of `tools/perf/Makefile`
  runs `tools/perf/tests/make`.
- Names not derived from the feature name: the `HAVE_` macro, the `CONFIG_`
  symbol, the `NO_` switch and the `supported_features[]` name; for
  example feature `libaio` gives `HAVE_AIO_SUPPORT`, `NO_AIO` and "aio".
- `HAVE_` macro: must be spelled the same in the `-D` of `Makefile.config`,
  the `#ifdef` in sources and the second argument of `FEATURE_STATUS()`.
- `CONFIG_` symbol: must be spelled the same in `$(call detected,...)` and
  in the `Build` files.
- `supported_features[]` name: must match what shell tests pass to
  `perf check feature`; the table in
  `tools/perf/Documentation/perf-check.txt` repeats the names but lacks
  some, for example "rust".
- `FEATURE_STATUS(name_, macro_)`: name string first, macro second.
- `IS_BUILTIN()` in `tools/include/tools/config.h`: 1 only when the macro
  is visible in `tools/perf/builtin-check.c` and defined as 1; a misspelled
  macro compiles and prints `OFF`.
- Macro defined in a header, not by `-D`: `builtin-check.c` must include
  that header, as it does `util/bpf-utils.h` for
  `HAVE_LIBBPF_STRINGS_SUPPORT`.
- `tools/perf/scripts/install-build-deps.sh`: maps each `test-<name>`
  source to a distro package in `fedora_pkg_for()` and `debian_pkg_for()`;
  a name with no case there is skipped silently by
  `make install-build-deps`.
