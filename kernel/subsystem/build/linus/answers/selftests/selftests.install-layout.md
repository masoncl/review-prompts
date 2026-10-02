- Helpers: every file in `tools/testing/selftests/kselftest/` is installed,
  `kselftest/ksft.py` included; see the `install -m 744` lines of `install` in
  `tools/testing/selftests/Makefile`.
- Listed by the `emit_tests` of `lib.mk` only if all hold: the test is in
  `TEST_GEN_PROGS`, `TEST_CUSTOM_PROGS` or `TEST_PROGS`; its directory is in
  `$(TARGETS)`; and `$(INSTALL_PATH)/<target>` exists when the emit loop runs.
- A directory whose install produced nothing is skipped with `Skipping
  non-existent dir`.
- `emit_tests` output: the sub-make's stdout is appended to
  `kselftest-list.txt` as is. Anything a test Makefile prints on stdout
  during that goal becomes a list entry.
- `bpf/Makefile` skips its feature checks for the `emit_tests` goal;
  `arm64/Makefile` defines its own `emit_tests`, which prints nothing off
  arm64.
- Listed name: `emit_tests` prints the basename. `run_kselftest.sh` changes
  into `<collection>/` and runs `./<basename>`, so the file must sit at the top
  of the installed target directory.
- `config` and `settings`: installed through `$(wildcard config settings)` in
  `INSTALL_RULE` of `lib.mk`, with no `TEST_` variable. The test Makefile is
  not in that list.
- `tools/testing/selftests/seccomp/Makefile`: has no `TEST_FILES` entry for
  its `settings` file; the wildcard installs it.
- `settings` in the installed tree: `run_one()` reads it from
  `<install root>/<collection>/settings`; `run_kselftest.sh` sets `BASE_DIR`
  to its own directory.
