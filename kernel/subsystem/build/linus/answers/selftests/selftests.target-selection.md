- `SKIP_TARGETS ?= bpf sched_ext` in `tools/testing/selftests/Makefile` is the
  only reason those two are not built by default. No toolchain or config test
  is made there.
- `SKIP_TARGETS` uses `filter-out`, which matches whole words: `SKIP_TARGETS=net`
  leaves `net/forwarding` and the other `net/` directories selected.
- `quicktest=1`: drops `timers` from the default list.
- `cpu-hotplug` and `memory-hotplug`: in `TARGETS` as well as in
  `TARGETS_HOTPLUG`. The default run includes them; `run_hotplug` runs their
  `run_full_test` target instead.
- `INSTALL_DEP_TARGETS := net/lib`: set when `TARGETS` holds the exact word
  `net`, `drivers/net` or `drivers/net/hw` and does not hold `net/lib`.
  `TARGETS=net/forwarding` alone does not add it.
- `drivers/net/hw`: named in that filter but absent from the default
  `TARGETS`, so it is built only when a user names it.
- `INSTALL_DEP_TARGETS` is computed before the `SKIP_TARGETS` filter and is
  not filtered by it. `SKIP_TARGETS=net/lib` does not remove it, and skipping
  `net` leaves it in place.
- `net/lib` added this way: built by `all`, copied by `install`, cleaned by
  `clean`. The `run_tests` loop and the emit loop iterate `$(TARGETS)` only, so
  it is not run and not listed.
