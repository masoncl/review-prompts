- Documented rule: `Documentation/dev-tools/kselftest.rst`, "Contributing new
  tests": "Don't cause the top-level "make run_tests" to fail if your feature
  is unconfigured", and "Do as much as you can if you're not root".
- `Documentation/dev-tools/kselftest.rst` does not give the value 4; it comes
  from `KSFT_SKIP` in `tools/testing/selftests/kselftest.h` and in
  `tools/testing/selftests/kselftest/ktap_helpers.sh`.
- `run_one()` in `tools/testing/selftests/kselftest/runner.sh`: maps
  `KSFT_PASS`, `KSFT_SKIP` and `KSFT_XFAIL` to an `ok` line; every other code
  becomes `not ok`.
- `ksft_finished()`: counts `ksft_cnt.ksft_xskip` towards the plan, so a C
  test that skipped every case with `ksft_test_result_skip()` exits
  `KSFT_PASS`.
- Shell variable names: `tools/testing/selftests/kselftest/ktap_helpers.sh`
  defines `KSFT_SKIP`; lowercase `ksft_skip` is defined by other libraries,
  for example `tools/testing/selftests/net/lib.sh`, or by the script itself.
- Shell, whole script: `prerequisite()` in
  `tools/testing/selftests/cpufreq/main.sh` calls `ktap_skip_all()` and then
  `exit "${KSFT_SKIP}"` for each missing prerequisite.
- `tools/testing/selftests/clone3/clone3.c` without root: `not_root()` is a
  per-test filter that gives `ksft_test_result_skip()`; it does not call
  `ksft_exit_skip()`.
- Harness, prerequisite checked in setup: `FIXTURE_SETUP(layout2_overlay)` in
  `tools/testing/selftests/landlock/fs_test.c`.
