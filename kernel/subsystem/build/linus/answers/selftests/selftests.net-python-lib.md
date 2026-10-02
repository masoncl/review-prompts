- `ksft_eq()`, `ksft_true()` and the other checks in
  `tools/testing/selftests/net/lib/py/ksft.py`: do not raise; `_fail()` prints
  and sets `KSFT_RESULT` to False, and the case keeps running.
- There is no ksft_false() in this tree.
- A check that fails before the case raises `KsftSkipEx` or `KsftXfailEx`:
  the line is `not ok ... # SKIP` or `not ok ... # XFAIL`, the totals count
  it as skip or xfail, and the exit status is 1.
- A deferred callback that raises after a skip or xfail gives the same
  `not ok` line with the directive.
- `defer()` outside a test case: raises `Exception`, because
  `GLOBAL_DEFER_ARMED` is False; see `defer.__init__()` in
  `tools/testing/selftests/net/lib/py/utils.py`.
- `ksft_run()` arms the queue only around the call of each case, so `defer()`
  in `main()` or in environment setup is not available.
- `tools/testing/selftests/drivers/net/lib/py/` re-exports `defer` and does
  not call it; environment teardown is `__exit__()` of the environment class.
- `ksft_run()` prints the `# Totals:` line; `ksft_exit()` prints nothing.
- `ksft_exit()`: `sys.exit(0 if KSFT_RESULT_ALL else 1)`; the Python library
  defines no named exit constants.
- A run in which every case skipped exits 0, not 4.
- `ksft_exit()` inside the `with` block of the environment: `__exit__()` still
  runs, because `sys.exit()` raises;
  `tools/testing/selftests/drivers/net/hw/nic_timestamp.py` does this.
