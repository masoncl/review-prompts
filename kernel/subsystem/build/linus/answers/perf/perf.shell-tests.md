- Discovery: `create_script_test_suites()` in
  `tools/perf/tests/tests-scripts.c`; there is no run_shell_tests() or
  shell_tests__dir() here.
- `shell_tests__dir_fd()`: tries, in order, `./tools/perf/tests/shell`,
  `./tests/shell` and `./source/tests/shell` relative to the current
  directory, then `tests/shell` and `source/tests/shell` beside the
  executable, then `tests/shell` under `get_argv_exec_path()`.
- Current directory first: an installed perf run from the top of a kernel
  tree runs that tree's scripts, not the installed ones.
- `is_shell_script()`: a test needs the `.sh` suffix as well as read and
  execute permission.
- `append_scripts_in_dir()`: skips entries whose name starts with `.`, does
  not descend into directories whose name starts with `base_`, and descends
  into every other directory with no depth limit.
- `lib` and `common`: not excluded by name; a file there becomes a test if it
  ends in `.sh`, is executable and has a description line.
- `base_` directories: run by a driver script, for example
  `tools/perf/tests/shell/perftool-testsuite_probe.sh`.
- `shell_test__description()`: the description is the first line that starts
  with `#` (after optional whitespace), is not `#!`, is not an SPDX
  identifier line, and has text; it need not be line two.
- ` (exclusive)`: `append_script()` looks for it anywhere in the description,
  with the leading space, and cuts the description there; text after it is
  lost.
- `shell_test__run()`: runs the script with `system()`, by absolute path, with
  ` -v` appended when `verbose` is set; only exit status 2 maps to
  `TEST_SKIP`.
- `workloads[]` in `tools/perf/tests/builtin-test.c`: holds more than the
  commonly remembered names; `workload__code_with_type` is present only under
  `HAVE_RUST_SUPPORT`. `perf test --list-workloads` prints the set.
- `--record-ctl fifo:ctl-fifo[,ack-fifo]`: `run_workload()` writes `enable`
  to the FIFO before calling the workload and `disable` after it, and waits
  for `ack` when an ack FIFO is given; see
  `tools/perf/tests/shell/coresight/deterministic.sh`.
- Workload symbols: the workload code is part of the perf binary, so a script
  that greps for a workload symbol can first call
  `skip_test_missing_symbol()` from
  `tools/perf/tests/shell/lib/perf_has_symbol.sh`, which exits 2 when perf
  lacks the symbol, as `tools/perf/tests/shell/record.sh` does.
