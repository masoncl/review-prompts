- `__bail()`: does not call `longjmp()`; for an `ASSERT_*` it calls
  `t->teardown_fn`, then `abort()`.
- `FIXTURE_TEARDOWN()` after a failed `ASSERT_*`: runs inside `__bail()`, in
  the process that asserted, before the `abort()`.
- `FIXTURE_TEARDOWN_PARENT()` after a failed `ASSERT_*`: not run by
  `__bail()`; the wrapper runs it after the grandchild has died.
- `ASSERT_*` failing in `FIXTURE_SETUP()`: no teardown of either kind runs;
  `*no_teardown` is still true.
- `TEST()`: `teardown_fn` is NULL, so `__bail()` only aborts.
- `trigger`: set by a failed check, cleared only when the handler loop
  finishes, by `SKIP()`, or by `__run_test()`; a passing check does not clear
  it.
- **Potentially unsafe usage**: a handler block that leaves with `return`,
  `goto` or `break`.
  - Unsafe: when another `ASSERT_*` or `EXPECT_*` runs afterwards in the same
    test; `trigger` is still 1, so that check runs its handler and an
    `ASSERT_*` aborts even though it passed.
  - Unsafe: when the code relies on the `ASSERT_*` to stop the test;
    `__bail()` is skipped, so nothing aborts.
  - Safe: when no check follows before the test ends, as the `goto` handlers in
    `TEST(uevent_filtering)` in
    `tools/testing/selftests/uevent/uevent_filtering.c`; `__EXPECT()` has set
    `KSFT_FAIL` before the handler runs.
  - Safe: leaving through `SKIP()`, which clears `trigger`, as the handler of
    `EXPECT_EQ()` in `TEST(clone3_cap_checkpoint_restore)` in
    `tools/testing/selftests/clone3/clone3_cap_checkpoint_restore.c` does.
- **Potentially unsafe usage**: no `;` after an `ASSERT_*` or `EXPECT_*`;
  `OPTIONAL_HANDLER()` ends in a `for` with no body.
  - Unsafe: when the next statement is part of the test; it becomes the
    handler and runs only when the check failed.
  - Safe: when a block or `TH_LOG()` meant as the handler follows, as after
    `ASSERT_GT()` in `TEST(clone3_cap_checkpoint_restore)` in
    `tools/testing/selftests/clone3/clone3_cap_checkpoint_restore.c`.
- **Unsafe usage**: relying on a failed `EXPECT_*` to fail a `TEST_SIGNAL()` or
  `TEST_F_SIGNAL()` test that then dies by the expected signal;
  `__wait_for_test()` sets `KSFT_PASS`.
  - Safe: `ASSERT_*`; its `SIGABRT` is tested before `t->termsig`.
