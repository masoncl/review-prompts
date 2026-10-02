- `ksft_finished()`: `ksft_exit(ksft_plan == ksft_cnt.ksft_pass +
  ksft_cnt.ksft_xpass + ksft_cnt.ksft_xfail + ksft_cnt.ksft_xskip)`.
- Success kinds: pass, xpass, xfail and skip; `ksft_xpass` is in the sum.
- Not in the sum: `ksft_fail` and `ksft_error`.
- `ksft_test_num()` is not what `ksft_finished()` compares; it gives the
  test number and the mismatch line in `ksft_print_cnts()`.
- Totals: `ksft_finished()` does not call `ksft_print_cnts()` itself;
  `ksft_exit_pass()` or `ksft_exit_fail()` does.
- A fail or error result within a full plan: the sum falls short, exit is
  `KSFT_FAIL`.
- More results than planned can hide a failure: with a plan of 3, three
  passes plus one fail make the sum equal the plan, so the exit is
  `KSFT_PASS`.
- `ksft_set_plan()` never called: `ksft_plan` is 0, so a run that reported
  only fail or error results exits `KSFT_PASS`; any successful result makes
  it exit `KSFT_FAIL`.
- `# Planned tests != run tests` in `ksft_print_cnts()`: tests `ksft_plan !=
  ksft_test_num()`, a different comparison from the exit condition, so it can
  appear on a `KSFT_PASS` exit and be absent on a `KSFT_FAIL` exit.
