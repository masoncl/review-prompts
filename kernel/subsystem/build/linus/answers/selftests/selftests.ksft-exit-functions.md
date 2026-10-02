- `ksft_exit_pass()`, `ksft_exit_fail()`, `ksft_exit_xfail()`,
  `ksft_exit_xpass()`: each calls `ksft_print_cnts()` before `exit()`; none
  exits silently.
- `ksft_exit_fail_perror()`: prints totals too, because it calls
  `ksft_exit_fail_msg()`, which prints the bail-out line and then
  `ksft_print_cnts()`.
- `ksft_exit_skip()` exits with `KSFT_SKIP` in both branches:

| State when called | Prints | Counter | Totals |
|---|---|---|---|
| `ksft_plan` is 0 and no result reported | `1..0 # SKIP msg` | none | not printed |
| `ksft_plan` is nonzero or a result was reported | `ok N # SKIP msg` | `ksft_xskip` | printed |

- `ksft_exit_skip()` right after `ksft_set_plan(n)` with `n` above 1: the
  runner still records skip from the exit code, but the test's own output has
  one result line against a plan of `n`.
