- Check in `__run_test()`: in the child, after `t->fn()` returns, if
  `__test_passed()` is true and `ksft_get_fail_cnt()` or
  `ksft_get_error_cnt()` is nonzero.
- On a hit: prints "Illegal usage of low-level ksft APIs in harness test" and
  sets `KSFT_FAIL`.
- Counters checked: only fail and error, counted from the
  `ksft_reset_state()` call made before `t->fn()`.
- `ksft_test_result_pass()`, `ksft_test_result_skip()`,
  `ksft_test_result_xfail()` and `ksft_test_result_xpass()` in a body: do not
  change the verdict; the test is reported as a plain pass, see
  `tools/testing/selftests/kselftest_harness/harness-selftest.expected`.
- Result line printed from a body: numbered from 1, since the counters were
  reset.
- `ksft_print_msg()` in a body: only prints; the harness calls it in the
  child itself.
- **Unsafe usage**: `ksft_test_result_fail()` or `ksft_test_result_error()` to
  fail a `TEST_F()` body or a `FIXTURE_SETUP()`; they run in the grandchild
  and the check reads the child's counters, so the test passes.
  - Safe: `ASSERT_*` or `EXPECT_*`, which set `_metadata->exit_code`.
- **Potentially unsafe usage**: `ksft_exit_skip()` in a body.
  - Unsafe: in a `TEST_F()` whose `FIXTURE_TEARDOWN()` must run; the process
    exits before it.
  - Safe: where no `FIXTURE_TEARDOWN()` has to run, as
    `test_clone3_supported()` called from
    `TEST(clone3_cap_checkpoint_restore)` in
    `tools/testing/selftests/clone3/clone3_cap_checkpoint_restore.c`; exit
    status 4 is read as `KSFT_SKIP` by `__wait_for_test()`.
  - Safe: `SKIP(return, ...)`, which stores the reason in `t->results` and
    returns through the teardown.
- `ksft_exit_skip()` in a body: prints a second plan line "1..0 # SKIP", and
  the harness reports the reason as "unknown".
- **Potentially unsafe usage**: `ksft_exit_fail_msg()` or `ksft_exit_fail()` in
  a body.
  - Unsafe: in a `TEST_F()` whose `FIXTURE_TEARDOWN()` must run; the process
    exits before it.
  - Safe: where no `FIXTURE_TEARDOWN()` has to run, as
    `TEST_F(guard_regions, uffd)` in
    `tools/testing/selftests/mm/guard-regions.c`, whose fixture uses
    `FIXTURE_TEARDOWN_PARENT()`; exit status 1 is read as `KSFT_FAIL` by
    `__wait_for_test()`, or copied to `exit_code` by the `TEST_F()` wrapper.
- `ksft_exit_fail_msg()` in a body: "Bail out!" and a "# Totals:" line enter
  the stream; `ksft_exit_fail()` adds only the "# Totals:" line.
