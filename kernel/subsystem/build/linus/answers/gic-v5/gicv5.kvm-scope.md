- `vgic_get_irq()` in `arch/arm64/kvm/vgic/vgic.c`: tests `vgic_is_v5(kvm)` before
  anything else and returns NULL for every intid, whatever its type field.
- `struct gicv5_vpe` (`include/linux/irqchip/arm-gic-v5.h`): one field,
  `bool resident`; no VPE table or doorbell state.
- `gicv5_vpe.resident`: only `vgic_v5_load()` and `vgic_v5_put()` use it, to
  skip the second load or put on the WFI path.
- Implemented PPIs: `vgic_v5_get_implemented_ppis()` sets the four timer PPIs
  (`GICV5_ARCH_PPI_CNTHP`, `GICV5_ARCH_PPI_CNTV`, `GICV5_ARCH_PPI_CNTHV`,
  `GICV5_ARCH_PPI_CNTP`) and `GICV5_ARCH_PPI_SW_PPI` unconditionally; for
  `GICV5_ARCH_PPI_PMUIRQ` see "PPI masks and iteration".
