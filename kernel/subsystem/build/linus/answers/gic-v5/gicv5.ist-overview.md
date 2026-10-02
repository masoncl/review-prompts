- One IST for the whole system: its state is `gicv5_global_data.ist`;
  `struct gicv5_irs_chip_data` holds no table state.
- `gicv5_irs_enable()`: does not write `GICV5_IRS_CR0`; it takes the first
  entry of `irs_nodes` and calls `gicv5_irs_init_ist()` on it, once, from
  `gicv5_init_common()`.
- `GICV5_IRS_CR0_IRSEN`: set earlier, for every IRS, by
  `gicv5_irs_init_bases()`.
- `GICV5_IRS_IST_CFGR` and `GICV5_IRS_IST_BASER`: accessed on that first IRS
  only; no other IRS has them programmed.
- `gicv5_irs_iste_alloc()`: maps level 2 tables through
  `per_cpu(per_cpu_irs_data, 0)`, the IRS of CPU 0, whichever CPU runs the
  call; with a two-level IST it returns `-ENOENT` if CPU 0 has no IRS.
- CPU 0's IRS need not be the first entry of `irs_nodes`; nothing in the
  driver ties the two together.
- LPI state after publishing: changed with `gic_insn()` system instructions
  in `drivers/irqchip/irq-gic-v5.c`, not through IRS MMIO registers.
