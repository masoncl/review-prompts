- `gic_cpu_sys_reg_init()`: `gic_get_pribits()` and `gic_has_group0()` run
  first, before the PMR write; `gic_write_bpr1(0)` sits between the PMR step
  and `gic_write_ctlr()`.
- `ICC_PMR_EL1` with `gic_prio_masking_enabled()` true: not written by
  `gic_cpu_sys_reg_init()`, apart from the probe-and-restore in
  `gic_has_group0()`.
  - It relies on `init_gic_priority_masking()` in `arch/arm64/kernel/smp.c`.
  - That runs in `secondary_start_kernel()` before `notify_cpu_starting()`,
    and in `smp_prepare_boot_cpu()`.
- Pseudo-NMI consistency check: compares this CPU with `cpus_have_group0` and
  `cpus_have_security_disabled`, which `gic_prio_init()` sets once on the boot
  CPU.
  - It runs only when `gic_supports_nmi()` is true.
  - A mismatch is a `WARN_ON()` and nothing more.
- `gic_cpu_config()` in `drivers/irqchip/irq-gic-common.c`: only writes; the
  wait is the `gic_redist_wait_for_rwp()` call that follows it in
  `gic_cpu_init()`.
- Boot-only inputs that every later `gic_cpu_init()` reads: `dist_prio_irq`
  (final after `gic_prio_init()`) and `gic_data.ppi_nr` (from
  `gic_update_rdist_properties()`); `gic_init_bases()` calls both first.
- SGI reachability check failing: `pr_crit()` for each CPU pair, and
  `pr_crit_once()` when RSS is needed and `gic_data.has_rss` is false.
  - There is no `WARN()`, no return value and no state change.
  - Per-CPU `has_rss` is read nowhere else; `gic_ipi_send_mask()` sends
    without consulting it.
