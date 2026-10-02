- Test that carries on after `SKIP()` with no later failure: reported
  `ok <n> <name> # SKIP <reason>`; see `__run_test()` in
  `tools/testing/selftests/kselftest_harness.h`.
- Kerneldoc above `SKIP()` says it forces a "pass"; the macro sets
  `_metadata->exit_code` to `KSFT_SKIP`, which `__test_passed()` counts as
  passed.
- Later failing `EXPECT_EQ()` or `ASSERT_EQ()` after `SKIP()`: the test is
  reported failed, in both `TEST()` and `TEST_F()`.
- `SKIP()` after a failed check: it overwrites `KSFT_FAIL` and clears
  `_metadata->trigger`, so the test is reported skipped.
- `SKIP(return, ...)` inside the block that follows `ASSERT_GE()` relies on
  that overwrite, as in `TEST(close_range_cloexec)` in
  `tools/testing/selftests/core/close_range_test.c`.
- `SKIP()` in `FIXTURE_SETUP()`: teardown does not run, for
  `FIXTURE_TEARDOWN()` and for `FIXTURE_TEARDOWN_PARENT()`.
- `SKIP(return, ...)` in a `TEST_F()` body: teardown does run.
- Placement in setup: before anything teardown would release, as
  `FIXTURE_SETUP(layout2_overlay)` in
  `tools/testing/selftests/landlock/fs_test.c` does.
