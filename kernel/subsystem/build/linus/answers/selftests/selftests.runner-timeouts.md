- `settings`: read inline by `run_one()` from `$BASE_DIR/$DIR/settings`; there
  is no kselftest_get_timeout() helper.
- `settings` under make: `BASE_DIR` is `$(selfdir)`, so the file is read from
  the source tree, even with a separate `$(OUTPUT)`.
- `tap_timeout()`: two nested calls,
  `/usr/bin/timeout --foreground "$kselftest_timeout" /usr/bin/timeout
  "$kselftest_timeout" $1`.
- `kselftest_override_timeout` under make: there is no make option, but
  `runner.sh` does not reset the variable, so a value in the environment takes
  effect; `run_kselftest.sh` clears it before parsing `-o`.
- `# timeout set to N` and `# overriding timeout to N`: appended to
  `$logfile`, which is the runner's stdout only by default.
- Missing utility: the test is `[ -x /usr/bin/timeout ]`, an absolute path, not
  a `$PATH` lookup; if it fails the program runs with no limit and no
  warning, and `# timeout set to N` is still printed.
