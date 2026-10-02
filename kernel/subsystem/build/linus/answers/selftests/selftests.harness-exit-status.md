- Every test skipped: exits 0; `test_harness_run()` has no special case and
  calls `ksft_exit(ret == 0)`.
- No test selected by the filters: also exits 0.
- `KSFT_XPASS`: on the passing side, with `KSFT_PASS`, `KSFT_XFAIL` and
  `KSFT_SKIP`.
- Exit 4 from `test_harness_run()`: only for `-l` and `-h`;
  `test_harness_argv_check()` returns `KSFT_SKIP` before any test runs.
- Unknown option: `test_harness_argv_check()` returns `KSFT_FAIL`.
- `test_harness_run()` after the tests: does not return; `ksft_exit()` calls
  `exit()`.
