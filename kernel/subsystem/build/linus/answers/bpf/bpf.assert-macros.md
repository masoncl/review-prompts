- Every `ASSERT_*` macro in `test_progs.h` expands to `CHECK()` with its own
  `static int duration`; both families fail through the same `_CHECK()` and
  `test__fail()`.
- `ASSERT_*` on success: prints the same PASS line as `CHECK()`.
- `ASSERT_*` on failure: prints `__func__`, the `name` argument, and, for
  the comparison macros such as `ASSERT_EQ()`, the values cast to
  `long long`; the expression is not stringified and the test name is not
  printed.
- **Potentially unsafe usage**: `ASSERT_FAIL()` as the only thing that marks
  a failure.
  - Unsafe: when nothing else fails the test; `ASSERT_FAIL()` expands to
    `CHECK(false, ...)`, which takes the pass branch of `_CHECK()`: no
    `test__fail()`, and the format string is not printed.
  - Safe: when the caller fails the test itself, as `process_subtest()` does
    with `PRINT_FAIL()` after `parse_test_spec()` returns an error.
  - Safe: `PRINT_FAIL()`, which calls `test__fail()` unconditionally.
