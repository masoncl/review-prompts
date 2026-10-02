- Target: a path listed in `TARGETS` in `tools/testing/selftests/Makefile`,
  not every directory that has a Makefile; for example
  `tools/testing/selftests/kmod` and `tools/testing/selftests/drivers/net/hw`
  are not in the list, so `tools/testing/selftests/Makefile` builds them only
  when a user adds them to `TARGETS`.
- Nested target: `drivers/net/bonding` is a target of its own beside
  `drivers/net`; the target path is also the collection name in
  `kselftest-list.txt`.
- `KSFT_INSTALL_PATH`: read only by `tools/testing/selftests/Makefile`;
  `tools/testing/selftests/lib.mk` sees `INSTALL_PATH` set per target.
- `TEST_INCLUDES`: files in a subdirectory of selftests, the target's own or
  another, copied with their relative path kept; this is how shared shell
  and Python libraries reach an installed tree.
- `struct ksft_count`: `ksft_cnt` and `ksft_plan` are `static` in
  `tools/testing/selftests/kselftest.h`, so there is one copy per translation
  unit that includes the header, not one per process.
- `ksft_finished()`: the only exit helper in `kselftest.h` whose exit code
  depends on `ksft_plan`; `ksft_exit_pass()` and `ksft_exit_fail()` only
  print a comment on a mismatch, through `ksft_print_cnts()`.
- Python `ksft`: two unrelated modules share the name.
  `tools/testing/selftests/kselftest/ksft.py` is a thin KTAP printer with
  pass, fail and skip only. `tools/testing/selftests/net/lib/py/ksft.py` is a
  case runner (`ksft_run()`) with its own checks, variants and xfail.
- `__fixture_list`: the only global list in
  `tools/testing/selftests/kselftest_harness.h`; it is initialised to
  `&_fixture_global`.
- `struct __test_metadata`: registered on its fixture's `tests` list by
  `__register_test()`, not on a global list; one object per `TEST()` or
  `TEST_F()`, reset and reused for every variant by `__run_test()`.
- `struct __test_xfail`: hangs on a variant's `xfails` list; `XFAIL_ADD()`
  works only for a test defined through `__TEST_F_IMPL()` (`TEST_F()`,
  `TEST_F_SIGNAL()`, `TEST_F_TIMEOUT()`) under a `FIXTURE_VARIANT_ADD()`
  variant, not for a plain `TEST()`.
- `struct __test_results`: one `MAP_SHARED` object for the whole run, attached
  to `t->results` only while that test runs; it carries the `SKIP()` reason
  back to the harness.
- `TEST()` processes: two; the body runs in the child that `__run_test()`
  forks.
- `FIXTURE_TEARDOWN_PARENT()`: the teardown runs in the wrapper process, the
  parent of the grandchild; it does not run in the harness process.
- `TEST_F()` metadata: `mmap()`ed `MAP_SHARED` by its constructor, which is
  how the grandchild's `exit_code` reaches the wrapper.
- `TEST()` metadata: an ordinary static object, so writes made in the child
  are not seen by the harness.
- Result path to the harness: the child's wait status in both cases;
  `__wait_for_test()` overwrites `t->exit_code` on every path.
