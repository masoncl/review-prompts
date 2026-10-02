- `DEFINE_SUITE()`: defines both the one-entry `struct test_case` array and
  the `struct test_suite`; a suite with several cases writes the array and
  the struct by hand.
- `TEST_SKIP`: is −2. A case that returns 1 is reported FAILED, through the
  `default:` case of `print_test_result()`.
- `check_leaks()`: `run_test_child()` calls it after the case returns; a file
  descriptor above 3 left open makes the child `abort()`, so the case is
  reported FAILED whatever it returned. Not run with `-F`.
- `setup` in `struct test_suite`: `build_suites()` calls it for every suite,
  also for `perf test list`; a negative return stops perf test before any
  test runs. It may replace `test_cases`, as `setup_pmu_events_suite()` in
  `tools/perf/tests/pmu-events.c` does.
- `arch_tests[]`: `tools/perf/tests/builtin-test.c` uses the arch file's array
  only when `__i386__`, `__x86_64__`, `__aarch64__` or `__powerpc64__` is
  defined; otherwise it defines its own empty static array, so a new
  architecture has to extend that `#if`.
- Exclusive and numbering: `build_suites()` puts every suite that has at
  least one exclusive case after all suites that have none, shell scripts
  included; marking a case exclusive changes the suite's number in
  `perf test list`.
- Suite with both kinds of case: `start_test()` decides per case, so the
  non-exclusive cases run in the parallel pass and the exclusive ones in the
  second pass; see `tests__basic_mmap` in `tools/perf/tests/mmap-basic.c`.
- `-F`: `cmd_test()` sets `sequential` too, so the exclusive flag then only
  affects list order.
