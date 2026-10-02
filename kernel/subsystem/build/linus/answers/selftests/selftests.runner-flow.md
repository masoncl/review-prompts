- `run_many()`: calls `run_one "$DIR" "$TEST"` directly unless `RUN_IN_NETNS`
  is set (`run_kselftest.sh -n`); the pipeline that captures the output is
  inside `run_one()`.
- Working directory: ``cd `dirname $TEST` `` in the runner's own shell, then
  `cd -`; `DIR` is not the `cd` target, it only builds the test name and
  the `settings` path.
- `TEST_PROGS` under make: bare names, so they run in the directory make
  entered, unless `building_out_of_srctree` is defined; then `run_tests` in
  `tools/testing/selftests/lib.mk` rsyncs them to `$(OUTPUT)` and they run
  there, like `TEST_GEN_PROGS`.
- stderr: merged into stdout with `2>&1` before the prefixing.
- Program output: appended to `$logfile`, which is the runner's stdout only by
  default.

  | Invocation | `logfile` |
  |---|---|
  | default | `/dev/stdout` |
  | `make summary=1`, `run_kselftest.sh -p` | `$per_test_log_dir/$BASENAME_TEST`, truncated per test |
  | `run_kselftest.sh -s` | `$BASE_DIR/output.log`, truncated once at option parsing |

- `per_test_log_dir`: `/tmp` by default; `run_kselftest.sh -p DIR` sets it and
  creates `DIR` if needed; make has no way to change it.
- `run_kselftest.sh -s`: does not set `per_test_logging`.
- `logfile`, `per_test_logging`, `per_test_log_dir`, `RUN_IN_NETNS`: assigned
  when `runner.sh` is sourced, so a value from the environment is overwritten.
