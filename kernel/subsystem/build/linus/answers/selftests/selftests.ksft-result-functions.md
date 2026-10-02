| Call | TAP line | Counter in `ksft_cnt` |
|---|---|---|
| `ksft_test_result_pass()` | `ok N msg` | `ksft_pass` |
| `ksft_test_result_fail()` | `not ok N msg` | `ksft_fail` |
| `ksft_test_result()` | pass line if the condition is true, else fail line | that function's |
| `ksft_test_result_skip()` | `ok N # SKIP msg` | `ksft_xskip` |
| `ksft_test_result_xfail()` | `ok N # XFAIL msg` | `ksft_xfail` |
| `ksft_test_result_xpass()` | `ok N # XPASS msg` | `ksft_xpass` |
| `ksft_test_result_error()` | `not ok N # error msg` | `ksft_error` |
| `ksft_test_result_report()` | line of the function it picks | that function's |
| `ksft_test_result_code()` | `ok N name # DIRECTIVE msg`; with no directive `ok N name #  msg` or `not ok N name #  msg` | by code |

- Directive position: the format-style functions print the directive before
  the message, never after it.
- `ksft_test_result_report()`: a macro `switch` over `KSFT_PASS`,
  `KSFT_FAIL`, `KSFT_XFAIL`, `KSFT_XPASS`, `KSFT_SKIP` that calls the
  matching format-style function; it does not call `ksft_test_result_code()`.
- `ksft_test_result_report()` with any other value: no `default` case, so
  nothing is printed and no counter moves; the result count then falls one
  short of the plan.
- `ksft_test_result_code()` with `KSFT_FAIL` or any unknown value: `not ok`,
  counts `ksft_fail`; it does not call `ksft_exit_fail_msg()`.
- `ksft_test_result_code()`: prints `test_name` before the directive, accepts
  a NULL `msg`, and appends `\n` itself.
- Every other result function prints the format as given, so the format must
  end in `\n`.
- Macros: only `ksft_test_result()` and `ksft_test_result_report()`; neither
  adds a function name to the output.
