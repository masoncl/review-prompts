- **Potentially unsafe usage**: a temporary file whose name is fixed in the
  script.
  - Unsafe: directly under a shared directory such as `/tmp`. `start_test()`
    in `tools/perf/tests/builtin-test.c` runs non-exclusive scripts in
    parallel, and the `runs_per_test` loop (`-r`) starts several copies of
    one such script together, so a name unique to the script still collides.
  - Safe: a fixed name inside a directory made by `mktemp -d`, as
    `tools/perf/tests/shell/script.sh` does.
- **Potentially unsafe usage**: `exit` after `trap trap_cleanup EXIT TERM INT`
  is installed.
  - Unsafe: when `cleanup` has not run first and `trap_cleanup` ends in
    `exit 1`. The EXIT trap runs `trap_cleanup`, so `exit 2` or `exit 0` is
    reported as failed by `shell_test__run()`.
  - Safe: call `cleanup`, which resets the trap, then exit; as
    `tools/perf/tests/shell/timechart.sh` does before `exit 2` and
    `tools/perf/tests/shell/record.sh` does before `exit $err`.
  - Safe: make the skip checks before the trap is installed, as
    `tools/perf/tests/shell/record.sh` does with `skip_test_missing_symbol`.
  - Safe: `trap cleanup EXIT` with a separate `TERM INT` trap that exits 1, as
    `tools/perf/tests/shell/data_validation.sh` does; the exit status is kept.
  - Safe: a `trap_cleanup` that ends in `exit ${err}`, with `err` set before
    each `exit`, as `check()` in `tools/perf/tests/shell/lock_contention.sh`
    does with `err=2`.
- `perf_record_with_retry()` in `tools/perf/tests/shell/lib/perf_record.sh`:
  makes its own `mktemp` log file on each call and records it in
  `PERF_RECORD_LOGS`; the script's `cleanup` has to call
  `perf_record_cleanup`, as `tools/perf/tests/shell/record.sh` does.
- `mktemp` templates: in-tree tests pass an absolute `/tmp/` template; the
  `__perf_test.` prefix is common but nothing checks for it.
- `rm -rf` of a directory variable: `tools/perf/tests/shell/script.sh` first
  checks that the path starts with its own `/tmp/` prefix.
- Removal on failure: not uniform in the tree;
  `tools/perf/tests/shell/inject_aslr.sh` keeps `temp_dir` when the exit code
  or `err` is non-zero.
- `__cmd_test()`: has no per-test timeout; on `SIGINT` or `SIGTERM` it sends
  the signal to each forked perf child, not to the script that child started
  with `system()`.
