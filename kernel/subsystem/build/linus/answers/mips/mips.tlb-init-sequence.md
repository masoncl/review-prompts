- Boot CPU: `trap_init()` calls `per_cpu_trap_init(true)`, which calls
  `tlb_init()`, before its first `set_handler()` or `set_except_vector()`;
  the TLB is set up before `trap_init()` installs any vector.
- Boot CPU, during `r4k_tlb_configure()`: `configure_status()` has already
  cleared `ST0_BEV` and, when `cpu_has_mips_r2_r6`,
  `configure_exception_vector()` has written EBase, but `trap_init()` has
  copied no handler to `ebase` yet; the refill handler is copied there by
  `build_tlb_refill_handler()`, at the end of `tlb_init()`.
- `per_cpu_trap_init()`: calls `tlb_init()` unconditionally; no test of
  `tlbsize` or `is_boot_cpu` guards it.
- `tlb_init()` in `arch/mips/mm/tlb-r4k.c`: does not call `setup_pw()`
  itself; `build_tlb_refill_handler()` does, under `cpu_has_ldpte`.
- Secondary CPU: `tlb_init()` still calls `build_tlb_refill_handler()`; only
  the code generation inside it is behind `run_once`, the per-CPU register
  setup in it runs again.
- Return from a power state: `per_cpu_trap_init()` is not called; its only
  callers are `trap_init()` and `start_secondary()`.
- Return from a power state: `cpu_pm_exit()` (for example from
  `cps_nc_enter()` in `drivers/cpuidle/cpuidle-cps.c`) runs
  `r4k_tlb_pm_notifier()`, which calls `r4k_tlb_configure()` and nothing
  else of `tlb_init()`.
- Status and EBase on that path: restored by a separate notifier,
  `trap_pm_notifier()` in `arch/mips/kernel/traps.c`.
- `CONFIG_CPU_R3K_TLB`: `tlb_init()` comes from `arch/mips/mm/tlb-r3k.c` and
  is `local_flush_tlb_from(0)` then `build_tlb_refill_handler()`, with no
  uniquification.
