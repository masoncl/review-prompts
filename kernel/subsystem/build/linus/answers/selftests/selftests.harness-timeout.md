- `__wait_for_test()`: uses no `alarm()` and no signal handler; it opens a
  pidfd with `__NR_pidfd_open` and waits in `poll()` for `t->timeout` seconds.
- pidfd open failure: the test fails with "unable to open pidfd" and the
  child is neither waited for nor killed.
- `timed_out`: a local of `__wait_for_test()`, not a field of
  `struct __test_metadata`.
- After the `SIGKILL`: `waitpid()` is called once with `WNOHANG`; its status is
  not used for a timed-out test.
- Wrapper child of a `TEST_F()`: in the killed group, so
  `FIXTURE_TEARDOWN_PARENT()` does not run either.
- Binary run directly: only the harness limit applies.
- `kselftest_override_timeout`: wins over the `settings` file.
- `timeout=0` in `settings`: `runner.sh` has no special case; the value is
  passed to `/usr/bin/timeout` unchanged.
- Harness and runner: neither reads the other's limit; a `TEST_F_TIMEOUT()`
  above the runner's value needs a `settings` file, as
  `tools/testing/selftests/rtc/settings` has.
