- Test that passed: `KSFT_XPASS`, printed `ok ... # XPASS`; `__test_passed()`
  counts it as passing.
- Test that skipped: also `KSFT_XPASS`, with the `SKIP()` reason as the
  diagnostic; `__test_passed()` is true for `KSFT_SKIP`.
- Test that failed in any way, including a timeout, an unexpected signal or a
  failed `ASSERT_*`: `KSFT_XFAIL`, printed `ok ... # XFAIL`.
- Diagnostic: "unknown" when the test stored no reason.
- `XFAIL_ADD()`: needs a variant from `FIXTURE_VARIANT_ADD()`; there is no
  form for `TEST()` or for a fixture without a named variant.
- `XFAIL_ADD()`: must come after the `TEST_F()` and the
  `FIXTURE_VARIANT_ADD()` it names; it refers to their static objects.
