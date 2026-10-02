- `kselftest.h` on the meaning: the only text is the comment above
  `ksft_test_result_error()`, `/* TODO: how does "error" differ from "fail"
  or "skip"? */`; the header defines no distinction.
- `Documentation/dev-tools/ktap.rst`: lists an "ERROR" directive, meaning the
  execution of a test failed due to a specific error given in the diagnostic
  data, and says the result line should be "not ok".
- Case: `ksft_test_result_error()` prints the directive in lower case,
  `# error`, where `Documentation/dev-tools/ktap.rst` writes "ERROR".
- `ksft_test_num()`: adds `ksft_error` to the other five counters, so an error
  result takes a test number; "ksft_finished pass condition" says what it
  does to the exit status.
- Exit codes: there is no kselftest exit code for error, so
  `ksft_test_result_report()` and `ksft_test_result_code()` cannot produce an
  error result, and no `ksft_exit_*` function exits with one.
