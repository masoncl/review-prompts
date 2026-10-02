- `tools/testing/selftests/net/lib.sh` installs no `trap`; sourcing it removes
  nothing at exit.
- Namespace removal at exit is set up by each test; in-tree forms include:
  - `trap cleanup_all_ns EXIT`, for example
    `tools/testing/selftests/net/hsr/hsr_ping.sh`
  - `defer cleanup_all_ns` plus `trap defer_scopes_cleanup EXIT`, for example
    `tools/testing/selftests/net/protodown.sh`
  - a `cleanup` function of the test that calls `cleanup_all_ns()`
- `defer` in `tools/testing/selftests/net/lib/sh/defer.sh`: commands run in
  `defer_scope_pop()`, which `in_defer_scope()` and `defer_scopes_cleanup()`
  call; `defer.sh` installs no trap.
- `tests_run()` wraps each test in `in_defer_scope()`, so a `defer` made inside
  a test function runs when that function returns.
- `setup_ns()` also sets `net.ipv4.conf.all.rp_filter` and
  `net.ipv4.conf.default.rp_filter` to 0 in each namespace.
- `setup_ns()` when `ip netns add` fails: removes the namespaces made earlier
  in the same call and returns `$ksft_skip`; it does not exit.
- `setup_ns()` does not check the result of the `lo` up command or of the two
  sysctl writes.
- `ret_set_ksft_status()`: `RET` becomes the higher-ranked of the old and new
  status, so a later fail replaces an earlier xfail or skip.
- `retmsg`: replaced only when the new status strictly outranks `RET`.
- `check_err()` records `$ksft_xfail` in place of `$ksft_fail` when
  `FAIL_TO_XFAIL` is `yes`; `xfail()` sets it, and `xfail_on_slow()` and
  `xfail_on_veth()` set it when their condition holds.
- `log_test()`: merges `RET` into `EXIT_STATUS` with
  `ksft_exit_status_merge()`, returns `$RET`, and does not reset `RET`.
- The two merges rank differently:

  | Merge | Used for | Rank, low to high |
  |---|---|---|
  | `ksft_status_merge()` | checks into `RET` | pass, xfail, skip, fail |
  | `ksft_exit_status_merge()` | `RET` into `EXIT_STATUS` | xfail, pass, skip, fail |

- `EXIT_STATUS` starts at 0 and xfail ranks below pass, so xfail results alone
  never change it; a script that ends with `exit $EXIT_STATUS` exits 0, not 2.
- `EXIT_STATUS` is the name of the global; there is no ksft_exit_status
  variable.
