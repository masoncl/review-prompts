- `lpi_xa` itself holds no reference. A new LPI starts at count 1, and that one
  reference is the one `vgic_add_lpi()` returns and the caller stores in
  `ite->irq`.
- `vgic_add_lpi()` produces the returned reference in one of three ways:
  `vgic_get_irq()` at entry, `vgic_try_get_irq_ref()` on an object found under
  the xarray lock, or `refcount_set()` on a new object.
- There is no vgic_irq_get_ref() here; the unconditional get is
  `vgic_get_irq_ref()` in `arch/arm64/kvm/vgic/vgic.h`.
- `vgic_get_irq_ref()`: only for callers that already hold a reference; at
  count zero it warns once and takes nothing.
- `ap_list` reference: dropped with `vgic_put_irq_norelease()` in
  `vgic_prune_ap_list()` and `vgic_flush_pending_lpis()`; vCPU teardown goes
  through the latter from `__kvm_vgic_vcpu_destroy()`.
