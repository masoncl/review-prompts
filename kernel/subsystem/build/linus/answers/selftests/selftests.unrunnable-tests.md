- Missing file: `# Warning: file $TEST is missing!`, then a plain
  `not ok N selftests: DIR: NAME`; it is a failure with `rc=$KSFT_FAIL`, not
  a `# SKIP`.
- No execute bit: not reported as a skip either; `run_one()` tries these in
  order:
  1. `./ksft_runner.sh` is executable: runs
     `./ksft_runner.sh ./$BASENAME_TEST`, with no warning.
  2. Otherwise prints `# Warning: file $TEST is not executable`; if the first
     line starts with `#!`, runs the file with that interpreter.
  3. Otherwise prints a plain `not ok N ...` and returns `KSFT_FAIL`.
- `ksft_runner.sh`: tried only after `[ -x "$TEST" ]` failed; an executable
  test in the same directory is run directly.
- `$kselftest_cmd_args` (from `KSELFTEST_<NAME>_ARGS`): appended only when the
  test itself is executable; the `ksft_runner.sh` and interpreter commands
  drop it.
- Directory with one: `tools/testing/selftests/net/packetdrill` is the only
  one; its `TEST_PROGS` are the `*.pkt` scripts, and its `Makefile` ships
  `ksft_runner.sh` through `TEST_INCLUDES`.
