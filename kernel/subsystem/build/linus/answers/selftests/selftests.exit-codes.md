- `KSFT_XFAIL` (2): has its own arm in `run_one()`; `ktap_test_xfail()` prints
  `ok N selftests: DIR: NAME # XFAIL`.
- `KSFT_FAIL` (1) and `KSFT_XPASS` (3): no arm; the `*` arm prints
  `not ok N ... # exit=1` and `# exit=3`.
- Arm labels: the shell variables `KSFT_PASS`, `KSFT_SKIP`, `KSFT_XFAIL` from
  `tools/testing/selftests/kselftest/ktap_helpers.sh`, plus `timeout_rc`;
  there is no skip_rc in this tree.
- Timeout (124): one line, `not ok N ... # TIMEOUT <secs> seconds`; no bare `#`
  line before it.
- Result lines: all printed by `__ktap_test()` in `ktap_helpers.sh`, which
  also advances `KTAP_TESTNO`.
- Failure bookkeeping: `ktap_test_fail()` increments `KTAP_CNT_FAIL`; there is
  no kselftest_failures_file in this tree.
