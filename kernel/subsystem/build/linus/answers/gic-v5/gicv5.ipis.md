- Backing: each IPI is an LPI; count is `GICV5_IPIS_PER_CPU * nr_cpu_ids`,
  with `GICV5_IPIS_PER_CPU` defined as `MAX_IPI`.
- `gicv5_irq_ipi_domain_alloc()`: makes one `irq_domain_alloc_irqs_parent()`
  call for the whole range; `gicv5_irq_lpi_domain_alloc()` picks each LPI.
- Routing: not done at allocation. `ipi_setup_lpi()` in
  `arch/arm64/kernel/smp.c`, reached from `set_smp_ipi_range_percpu()`, calls
  `irq_force_affinity()` for each CPU, so the target may be offline.
- `gicv5_ipi_send_single()`: calls `irq_chip_retrigger_hierarchy()`, not
  `irq_chip_set_parent_state()`; that reaches `gicv5_lpi_irq_retrigger()` and
  ends in `GIC CDPEND`.
- `gicv5_ipi_irq_chip`: has no `irq_retrigger` of its own;
  `irq_chip_retrigger_hierarchy()` starts at the parent `irq_data`.
- Send to a mask: `arm64_send_ipi()` loops over the mask and calls
  `__ipi_send_single()` with that CPU's own descriptor.
- IPI allocation failure in `gicv5_smp_init()`: `WARN()` and return;
  `set_smp_ipi_range_percpu()` is not called.
