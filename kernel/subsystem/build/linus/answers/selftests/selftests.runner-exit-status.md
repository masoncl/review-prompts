- `run_kselftest.sh`: exits `KSFT_FAIL` (1) by default when `KTAP_CNT_FAIL` is
  not 0; `ERROR_ON_FAIL=true` is the default.
- `-f` / `--no-error-on-fail`: sets `ERROR_ON_FAIL=false`, so the script exits
  0 whatever failed.
- -e / --error-on-fail: not an option here; an unknown option reaches
  `usage 1`, which exits 1 before any test runs.
- What counts as a failure: every `not ok` from `run_one()`, since each is
  printed by `ktap_test_fail()`; that includes timeouts, missing files and
  non-executable files that `run_one()` cannot run.
- `# SKIP` and `# XFAIL` results: do not increment `KTAP_CNT_FAIL`.
- `make run_tests`, `make kselftest`: exit 0 on test failures; `RUN_TESTS` in
  `tools/testing/selftests/lib.mk` does not read `KTAP_CNT_FAIL`, and there is
  no make equivalent of `ERROR_ON_FAIL`.
