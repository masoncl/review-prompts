- First test in `vgic_v4_load()` and `vgic_v4_put()`:
  `vgic_supports_direct_irqs()`, not `vgic_supports_direct_msis()`; it is
  true when either `vgic_supports_direct_msis()` or
  `vgic_supports_direct_sgis()` is.
- `vgic_v4_load()`: also returns 0 with the vPE left non-resident when
  `IN_WFI` is set.
- `vgic_v3_load()` and `vgic_v3_put()`: return through
  `vgic_v3_load_nested()` or `vgic_v3_put_nested()` when
  `vgic_state_is_nested()`, and then do not call `vgic_v4_load()` or
  `vgic_v4_put()`.
- `vgic_v4_want_doorbell()`: true when `IN_WFI` is set; otherwise false
  unless `vcpu_has_nv()`, and then the value of `IN_NESTED_ERET`.
- `IN_NESTED_ERET`: set in `kvm_emulate_nested_eret()` around
  `kvm_arch_vcpu_put()` and `kvm_arch_vcpu_load()`.
- `KVM_REQ_RELOAD_GICv4`: raised only in `vgic_mmio_write_v3_misc()`, on a
  guest write to `GICD_CTLR` that changes `dist->enabled` while
  `vgic_supports_direct_sgis()` is true.
- A change of `nassgireq` alone: calls `vgic_v4_configure_vsgis()` and
  raises no request.
- `vgic_mmio_uaccess_write_v3_misc()`: sets `dist->enabled` from userspace
  and raises no request.
- `vgic_v4_request_vpe_irq()`: is `request_irq()` for the doorbell, unrelated
  to `KVM_REQ_RELOAD_GICv4`.
