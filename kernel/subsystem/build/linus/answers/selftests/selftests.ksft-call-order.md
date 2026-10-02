- Top comment of `tools/testing/selftests/kselftest.h`: calls the file the
  "low-level kselftest framework" and says "When possible, please use
  kselftest_harness.h instead."
- The comment gives no criterion beyond "when possible"; it does not mention
  fixtures, variants or test size.
- `ksft_print_header()`: sets stdout line buffered with `setvbuf()` before
  anything else, so a test that skips the call can duplicate buffered output
  across `fork()`.
- `ksft_print_header()`: prints `TAP version 13` only when the environment
  variable `KSFT_TAP_LEVEL` is unset.
- Whole-program skip for a missing prerequisite: `ksft_exit_skip()` goes
  after `ksft_print_header()` and before `ksft_set_plan()`, as `main()` in
  `tools/testing/selftests/mm/hugetlb-soft-offline.c` does; "Exit functions"
  says what it prints when called later.
