- `FIXTURE_SETUP()` and one teardown macro: both required once a fixture has a
  `TEST_F()`; the wrapper from `__TEST_F_IMPL()` calls both functions and reads
  a flag that only `FIXTURE_TEARDOWN()` or `FIXTURE_TEARDOWN_PARENT()` defines.
- `TEST_F_SIGNAL()`: the fixture form of `TEST_SIGNAL()`.
- `FIXTURE_TEARDOWN_PARENT()`: the only parent form; setup has none.
- `FIXTURE_DATA()`: names the struct type of `self`, for a helper that takes
  `self` as a parameter; `FIXTURE()` expands to it.
- Signal plus timeout: no macro other than the internal `__TEST_F_IMPL()`
  takes both; `TEST_F_SIGNAL()` fixes the timeout at `TEST_TIMEOUT_DEFAULT`,
  `TEST_F_TIMEOUT()` fixes the signal at -1.
- `SIGABRT` as the expected signal of `TEST_SIGNAL()` or `TEST_F_SIGNAL()`:
  cannot pass; `__wait_for_test()` tests for `SIGABRT` before `t->termsig`.
- Missing from the `:functions:` list in
  `Documentation/dev-tools/kselftest.rst`: `TEST_F_SIGNAL()`,
  `TEST_F_TIMEOUT()`, `FIXTURE_TEARDOWN_PARENT()` and `XFAIL_ADD()`;
  `TEST_SIGNAL()` is in the list.
- `TEST_F_SIGNAL()` and `TEST_F_TIMEOUT()`: have no kernel-doc comment, so
  adding them to the list alone renders nothing.
- `FIXTURE_TEARDOWN_PARENT()`, `XFAIL_ADD()` and `SKIP()`: have a kernel-doc
  comment and are not listed.
