- `MIPS_CPU_MCHECK`: set in one place, `decode_configs()`; legacy R4000-class
  probe code does not set it.
- `cpu_has_mcheck`: `__isa_ge_or_opt(1, MIPS_CPU_MCHECK)` in
  `arch/mips/include/asm/cpu-features.h`, so it is constant true when
  `MIPS_ISA_REV` is at least 1.
- Platform overrides: `cpu-feature-overrides.h` files force `cpu_has_mcheck`
  to 0 or 1; for example
  `arch/mips/include/asm/mach-loongson64/cpu-feature-overrides.h` forces 0,
  so no handler is installed there although `decode_configs()` sets the bit.
- Without the handler: ExcCode 24 keeps `handle_reserved`, and
  `do_reserved()` panics.
- `do_mcheck()`: calls `dump_tlb_regs()` and `dump_tlb_all()` only when
  `ST0_TS` was set in `regs->cp0_status`; it ends in `panic()`, not `die()`.
- `ST0_TS`: cleared by `configure_status()`, which runs before `tlb_init()`
  in `per_cpu_trap_init()` and again from `trap_pm_notifier()`.
