- `TEST_F()`: three processes; the harness forks a child in `__run_test()`, and
  the wrapper from `__TEST_F_IMPL()` forks a grandchild from that child.
- Grandchild of a `TEST_F()`: runs `FIXTURE_SETUP()`, the body and
  `FIXTURE_TEARDOWN()`.
- Child, before `t->fn()`: `setpgrp()`, then `ksft_reset_state()` in
  `kselftest.h`, which zeroes the `ksft_cnt` counters and `ksft_plan`.
- Crash in a `TEST_F()` body with `FIXTURE_TEARDOWN()`: teardown does not run.
- Crash in a `TEST_F()` body with `FIXTURE_TEARDOWN_PARENT()`: teardown runs in
  the wrapper before it re-raises the signal, if setup had completed.
