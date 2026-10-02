- `gic_smp_init()`: passes a literal 8 to `irq_domain_alloc_irqs()` and to
  `set_smp_ipi_range()`; the count is not derived from `NR_IPI` or `MAX_IPI`.
- `set_smp_ipi_range()` on arm64: an inline wrapper in
  `arch/arm64/include/asm/smp.h` for `set_smp_ipi_range_percpu()` with
  `ncpus` 0.
- No headroom: `set_smp_ipi_range_percpu()` does `WARN_ON(n < MAX_IPI)` and
  sets `nr_ipi` to `min(n, MAX_IPI)`.
  - `MAX_IPI` is 8 on arm64 (`enum ipi_msg_type` in
    `arch/arm64/include/asm/smp.h`) and 8 on arm (`arch/arm/kernel/smp.c`).
  - A ninth entry in `enum ipi_msg_type` trips the `WARN_ON()` and gets no
    interrupt.
- `IPI_CPU_BACKTRACE` and `IPI_KGDB_ROUNDUP`: NMIs only when
  `ipi_should_be_nmi()` returns true, which needs
  `system_uses_irq_prio_masking()`.
  - Otherwise `ipi_setup_sgi()` requests them as ordinary per-CPU IRQs.
- RS field: there is no MPIDR_TO_SGI_RS_VALUE here; `MPIDR_TO_SGI_RS()` in
  `drivers/irqchip/irq-gic-v3.c` does that.
- The driver's own limit is 16, not 8, everywhere except `gic_smp_init()`:
  - `SGI_NR` sizes the group and priority setup in `gic_cpu_init()`.
  - `gic_irq_domain_translate()` accepts any one-cell fwspec below 16.
  - `gic_ipi_send_mask()` rejects only `d->hwirq >= 16`.
- `gic_send_sgi()`: shifts `irq` into place without masking it; the
  `WARN_ON()` in `gic_ipi_send_mask()` is the only range check.
