- `CONFIG_PROVE_RAW_LOCK_NESTING=y`: `LD_WAIT_CONFIG` is its own value between
  `LD_WAIT_SPIN` and `LD_WAIT_SLEEP`.
- `CONFIG_PROVE_RAW_LOCK_NESTING=n`: `LD_WAIT_CONFIG = LD_WAIT_SPIN`
  (`include/linux/lockdep_types.h`); it never equals `LD_WAIT_SLEEP`, so under
  `CONFIG_PROVE_LOCKING` a sleeping lock under a spinning lock is reported
  either way.
- Default depends on the architecture (`lib/Kconfig.debug`): with
  `ARCH_SUPPORTS_RT` the option has no prompt and is `y` whenever
  `CONFIG_PROVE_LOCKING` is on; without `ARCH_SUPPORTS_RT` it has a prompt and
  no default, so it is off unless chosen.
- `ARCH_SUPPORTS_RT`: defined in `arch/Kconfig`; search `arch/` for
  `select ARCH_SUPPORTS_RT`, for example x86 and arm64.
- Also controlled by the option: `lockdep_assert_RT_in_threaded_ctx()`
  (`include/linux/lockdep.h`, used by `complete_all()`) is empty without it,
  and `wait_context_tests()` in `lib/locking-selftest.c` is not run.
