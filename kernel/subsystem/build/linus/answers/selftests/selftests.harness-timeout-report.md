- `TEST_F_TIMEOUT()`: the only macro that takes a limit, apart from the
  internal `__TEST_F_IMPL()` it expands to; `TEST()`, `TEST_SIGNAL()`,
  `TEST_F()` and `TEST_F_SIGNAL()` are fixed at `TEST_TIMEOUT_DEFAULT`.
- **Unsafe usage**: writing `_metadata->timeout` in a test body to change the
  limit; the harness process reads `t->timeout` in `__wait_for_test()` right
  after the fork, and a `TEST()` body writes a private copy.
  - Safe: `TEST_F_TIMEOUT()`, as in `tools/testing/selftests/rtc/rtctest.c`.
- Report for an expired limit: `KSFT_FAIL`, set in the `timed_out` branch of
  `__wait_for_test()`.
