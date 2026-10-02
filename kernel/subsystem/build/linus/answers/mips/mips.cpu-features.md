- `cpu_has_` macros: read `cpu_data[0]`, the boot CPU's `struct cpuinfo_mips`,
  through `__opt()`, `__ase()` and `__isa()`; the cache macros such as
  `cpu_has_dc_aliases` read `cpu_data[0].dcache.flags` or
  `cpu_data[0].icache.flags`.
- `cpu_has_fpu`: the one macro that reads `current_cpu_data`, under
  `CONFIG_MIPS_FP_SUPPORT` and unless a platform override defines it as 0;
  `raw_cpu_has_fpu` reads `raw_current_cpu_data`.
- `cpu_probe()` fills `current_cpu_data` on each CPU, but a bit set or
  cleared only in a secondary CPU's entry does not change any `cpu_has_` macro
  other than `cpu_has_fpu`.
- Macros with no `#ifndef`, which a platform cannot override directly:
  `cpu_has_mipsmt_pertccounters` and the shortcut macros, for example
  `cpu_has_mips_r2_r6`.
- Override file: chosen by the `-I` flags in the platform's `Platform` file,
  for example `arch/mips/ath79/Platform`; `arch/mips/Makefile` appends
  `arch/mips/include/asm/mach-generic` last, as the fallback.
- An override need not be a literal: `cpu_has_dc_aliases` is
  `(PAGE_SIZE < 0x4000)` on some platforms, and
  `arch/mips/include/asm/mach-cavium-octeon/cpu-feature-overrides.h` defines
  `cpu_has_rixi` as a run-time test of `cpu_data[0].cputype`.
- An override changes the macro only, not the probed bits; code that tests
  `c->options` or `c->dcache.flags` directly can disagree with the macro.
- Hidden reads of `current_cpu_data`, for example: `cpu_has_fpu` and
  `current_cpu_type()` in `arch/mips/include/asm/cpu-type.h`;
  `boot_cpu_type()` reads `cpu_data[0]`.
- **Potentially unsafe usage**: reading `current_cpu_data`.
  - Unsafe: after boot, in preemptible context where the task can migrate;
    the value may belong to another CPU, also on identical CPUs, because
    `asid_cache`, `udelay_val`, `globalnumber` and `htw_seq` are per-CPU
    state; `debug_smp_processor_id()` warns under `CONFIG_DEBUG_PREEMPT`.
  - Safe: in a context that `check_preemption_disabled()` in
    `lib/smp_processor_id.c` accepts: non-zero preempt count, interrupts
    disabled, per-CPU thread, migration disabled, or `system_state` before
    `SYSTEM_SCHEDULING`.
  - Safe: under `local_irq_save()`, as `local_flush_tlb_all()` in
    `arch/mips/mm/tlb-r4k.c` does.
  - Safe: during early boot, as `cpu_probe()` called from `setup_arch()`.
- `raw_current_cpu_data`: skips the `CONFIG_DEBUG_PREEMPT` check and nothing
  else; where the task can migrate, the value is right only if it is the same
  on every CPU.
