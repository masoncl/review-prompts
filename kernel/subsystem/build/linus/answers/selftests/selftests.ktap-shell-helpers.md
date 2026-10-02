- `ktap_finished()` in `tools/testing/selftests/kselftest/ktap_helpers.sh`:
  exits `$KSFT_PASS` when `KTAP_CNT_PASS` + `KTAP_CNT_SKIP` +
  `KTAP_CNT_XFAIL` equals `KSFT_NUM_TESTS`, otherwise `$KSFT_FAIL`.
- `KTAP_CNT_FAIL`: not in the sum that `ktap_finished()` tests; a failure
  changes the exit status only because it leaves the sum short of the plan.
- `ktap_finished()` calls `ktap_print_totals()` and `exit`; it does not call
  `ktap_exit_fail_msg()`.
- `KSFT_NUM_TESTS` starts at 0, so a script that reports a pass without
  calling `ktap_set_plan()` and ends in `ktap_finished()` exits `$KSFT_FAIL`.
- `ktap_test_xfail()` and `ktap_test_result()`: both exist under those names.
- `ktap_skip_all()`: only prints `1..0 # SKIP ...`; the caller runs
  `exit "$KSFT_SKIP"` itself.
- There is no ktap_exit_pass() in this tree.
- Installed layout: the `install` target of
  `tools/testing/selftests/Makefile` copies `kselftest/ktap_helpers.sh` to
  `$(INSTALL_PATH)/kselftest/`, whatever `TARGETS` holds.
- `TEST_INCLUDES`: for the installed tree a test Makefile does not need to
  list the helper; only `tools/testing/selftests/net/packetdrill/Makefile`
  does.
- Example of the whole sequence ending in `ktap_finished()`:
  `tools/testing/selftests/power_supply/test_power_supply_properties.sh`.
- `tools/testing/selftests/dt/test_unprobed_devices.sh`: shows the `DIR` and
  `source` lines and `ktap_skip_all()`, but does not call `ktap_finished()`;
  it calls `ktap_print_totals()` and exits with its own `retval`.
- `tools/testing/selftests/cpufreq/main.sh` and
  `tools/testing/selftests/mm/ksft_kmemleak_confirm.sh` source the helper;
  no script under the pidfd or watchdog selftests does.
