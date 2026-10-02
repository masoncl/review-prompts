- Newline: `ksft_exit_skip()` adds none; the message has to end in `\n`
  itself.
- Misuse named by the FIXME in `ksft_exit_skip()`: calling it when "some tests
  have already been run or a plan has been printed".
- Replacement named by the FIXME: `ksft_test_result_skip()` or
  `ksft_exit_fail_msg()`; it does not mention `ksft_finished()`.
- `test_membarrier_query()`, and `test_clone3_supported()` in the plain C
  clone3 programs such as `tools/testing/selftests/clone3/clone3.c`: `main()`
  calls `ksft_set_plan()` first, so their skip takes the `ok <n> # SKIP` form,
  which is the case the FIXME calls misuse.
- Skip before the plan, giving `1..0 # SKIP`: for example `main()` in
  `tools/testing/selftests/mm/soft-dirty.c` and
  `tools/testing/selftests/mm/mseal_test.c`.
