- Exit status 3 (`KSFT_XPASS`): no case in `run_one()`, so it is recorded as
  `not ok ... # exit=3`; `ksft_exit_xpass()` is a failure to the runner,
  although `ksft_finished()` counts xpass results as success.
- `Documentation/dev-tools/kselftest.rst` names no exit code and does not
  mention `KSFT_SKIP`.
- `Documentation/dev-tools/kselftest.rst` has two rules that apply: "Don't
  cause the top-level "make run_tests" to fail if your feature is
  unconfigured", and output "must conform to the TAP standard" with the
  `kselftest.h` or `kselftest_harness.h` wrappers used "for pass, fail, exit,
  and skip messages".
- **Potentially unsafe usage**: ending `main()` with `return 0` or an
  unconditional `ksft_exit_pass()` after per-case results were reported.
  - Unsafe: when a `not ok` result can have been reported before that point;
    `run_one()` reads only the exit status and records `ok`.
  - Safe: end with `ksft_finished()` when no more results than planned can
    be reported, as `main()` in
    `tools/testing/selftests/mm/hugetlb-soft-offline.c` does.
  - Safe: test `ksft_get_fail_cnt()` and call `ksft_exit_fail_msg()` when it
    is nonzero, before `ksft_exit_pass()`, in a test that reports no error
    results, as `main()` in `tools/testing/selftests/mm/mkdirty.c` does.
- **Unsafe usage**: exiting with a nonzero status other than `KSFT_SKIP` or
  `KSFT_XFAIL` when a feature or config option is missing; `run_one()`
  records `not ok`, which breaks the "unconfigured" rule in
  `Documentation/dev-tools/kselftest.rst`.
  - Safe: call `ksft_exit_skip()` before `ksft_set_plan()`, as `main()` in
    `tools/testing/selftests/mm/hugetlb-soft-offline.c` does; `run_one()`
    records `ok ... # SKIP` for exit status 4.
