- `harness-selftest.sh`: applies no filter; it runs `diff -u` on the raw
  output, and the exit status of `diff` is the verdict.
- Captured: stdout only, into `harness-selftest.seen` in the current
  directory; `harness-selftest.c` defines `TH_LOG_STREAM` as `stdout` so the
  logs are included.
- Harness output written straight to `stderr`: not compared.
- `harness-selftest.expected`: holds the `__LINE__` of every `TH_LOG()` and
  failed check, so any edit that moves lines in `harness-selftest.c` must
  update it.
- `harness-selftest.expected`: also holds the plan, the "Starting ... tests"
  line and the "# Totals:" line, so a change to what `kselftest.h` prints, or
  an added test, must update it.
- Not exercised by `harness-selftest.c`: `SKIP()`, `FIXTURE_VARIANT_ADD()`,
  `XFAIL_ADD()`, `TEST_F_SIGNAL()` and a body that forks; a change to their
  output does not fail this test.
