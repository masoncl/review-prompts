- DT, ITT and L1 IST entries: `__le64`, read with `le64_to_cpu()` and
  stored with `cpu_to_le64()`; see `gicv5_its_map_event()` in
  `drivers/irqchip/irq-gic-v5-its.c` and `gicv5_irs_iste_alloc()` in
  `drivers/irqchip/irq-gic-v5-irs.c`.
- L2 and linear IST: held as `void *` in `gicv5_irs_iste_alloc()` and
  `gicv5_irs_init_ist_linear()`; the kernel never reads or writes an entry
  in them, so they have no entry type.
- `__le32`: not used anywhere in the GICv5 drivers.
