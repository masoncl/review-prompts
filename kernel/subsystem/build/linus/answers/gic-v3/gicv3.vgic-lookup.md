- `vgic_get_irq()` on a private ID: returns NULL with no warning.
- `vgic_get_irq()` on a GICv5 VM: returns NULL for every ID; the
  `vgic_is_v5()` test is its first statement.
- SPI index: `VGIC_NR_PRIVATE_IRQS` is subtracted first, then the result is
  clamped with `array_index_nospec(intid, nr_spis)`.
- `vgic_get_vcpu_irq()` with a NULL `vcpu`: `WARN_ON()` and NULL.
- `vgic_get_vcpu_irq()` picks the private branch with `__irq_is_sgi()` and
  `__irq_is_ppi()` on the VM's model; the GICv5 branch indexes by
  `vgic_v5_get_hwirq_id()` and bounds and clamps against
  `VGIC_V5_NR_PRIVATE_IRQS`.
- Neither function tests `private_irqs` or `spis` for NULL; `nr_spis` can be
  non-zero (set through `KVM_DEV_ARM_VGIC_GRP_NR_IRQS`) before
  `kvm_vgic_dist_init()` allocates `spis`. Callers such as
  `kvm_vgic_inject_irq()` test `vgic_initialized()` first.
- Only an LPI result carries a reference. A missing `vgic_put_irq()` is a leak
  only where the ID can be an LPI; `kvm_vgic_set_owner()` omits the put after
  rejecting everything but PPIs and SPIs.
