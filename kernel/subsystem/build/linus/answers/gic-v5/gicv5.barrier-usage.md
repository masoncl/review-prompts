- `gsb_sys()` and `gsb_ack()`: defined in
  `arch/arm64/include/asm/barrier.h`.
- Encodings: `GSB_SYS_BARRIER_INSN` and `GSB_ACK_BARRIER_INSN` in
  `arch/arm64/include/asm/sysreg.h`, built with `__SYS_BARRIER_INSN()`;
  there are no macros named GSB_SYS or GSB_ACK.
- Kernel callers: `gsb_sys()` only in `gicv5_iri_irq_mask()`, `gsb_ack()`
  only in `gicv5_handle_irq()`.
- Every other `gic_insn()` site has no GSB after it: CDEN, CDPRI, CDAFF,
  CDPEND, CDHM, CDDI and CDEOI have nothing, CDRCFG has `isb()`.
- IRS and ITS table memory: not ordered with `gsb_sys()`; for example
  `drivers/irqchip/irq-gic-v5-irs.c` uses `dsb(ishst)` or
  `dcache_clean_inval_poc()` before the MMIO write.
- `ICC_*` register writes: not every one is followed by `isb()`; for example
  `write_ppi_sysreg_s()` and the `SYS_ICC_CR0_EL1` write in
  `gicv5_cpu_enable_interrupts()` have none.
- **Potentially unsafe usage**: a `gic_insn()` with no `gsb_sys()` after it.
  - Unsafe: when the caller must be able to rely on the effect on return,
    as SPI/LPI `irq_mask` must for lazy disable.
  - Safe: when completion in finite time is enough, as in
    `gicv5_iri_irq_unmask()`; its comment cites `R_XCLJC` as the only
    requirement.
- **Unsafe usage**: ending a PPI `irq_mask` or `irq_unmask` after the
  `SYS_ICC_PPI_ENABLER0_EL1` or `SYS_ICC_PPI_ENABLER1_EL1` write with no
  `isb()`.
  - Safe: write, then `isb()`, as `gicv5_ppi_irq_mask()` and
    `gicv5_ppi_irq_unmask()` do; see "Synchronisation after mask and
    unmask".
