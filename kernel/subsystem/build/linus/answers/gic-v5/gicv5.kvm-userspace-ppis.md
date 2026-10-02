- Drivable PPIs: only `GICV5_ARCH_PPI_SW_PPI`; `vgic_v5_init()` sets
  `userspace_ppis` to that bit anded with `impl_ppi_mask`.
- Attribute: `KVM_DEV_ARM_VGIC_USERSPACE_PPIS` in
  `KVM_DEV_ARM_VGIC_GRP_CTRL`; `vgic_v5_get_attr()` reads it through
  `vgic_v5_get_userspace_ppis()`.
- Value returned: two `u64`; the second is always 0.
- Before `KVM_DEV_ARM_VGIC_CTRL_INIT`: the read succeeds and returns 0.
- `vgic_lazy_init()`: returns `-EBUSY` for a GICv5 guest that is not
  initialised, for both PPI and SPI.

| Type | Checks, in order | Then |
|---|---|---|
| `KVM_ARM_IRQ_TYPE_PPI` | vCPU exists; number < `VGIC_V5_NR_PRIVATE_IRQS`; bit set in `userspace_ppis`; each failure is `-EINVAL` | `vgic_v5_make_ppi()`, `kvm_vgic_inject_irq()` with `NULL` owner |
| `KVM_ARM_IRQ_TYPE_SPI` | none on the number | `vgic_v5_make_spi()`, `kvm_vgic_inject_irq()`; `vgic_get_irq()` returns `NULL`, so the result is `-EINVAL` |
