- `vgic_get_irq()`: takes `(kvm, intid)`, serves SPIs and LPIs only, and
  returns NULL for a GICv5 VM.
- Private interrupts: looked up with `vgic_get_vcpu_irq()`, which returns a
  pointer into `private_irqs` and takes no count.
- An LPI with count 0 can still be in `lpi_xa`; `vgic_try_get_irq_ref()` fails
  on it, so `vgic_get_lpi()` returns NULL.
- Freeing an LPI that was stored in `lpi_xa`, always with `kfree_rcu()`:
  - `vgic_release_lpi_locked()`, from the final `vgic_put_irq()`;
  - `vgic_release_lpi_locked()`, from `vgic_release_deleted_lpis()`;
  - `vgic_add_lpi()` in `arch/arm64/kvm/vgic/vgic-its.c`, when it replaces a
    dead entry for the same INTID.
