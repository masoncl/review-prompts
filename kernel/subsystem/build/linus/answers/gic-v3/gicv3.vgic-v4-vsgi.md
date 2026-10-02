- `vgic_supports_direct_sgis()`: returns the per-VM `nassgicap`, not the host
  capability; without it `GICD_CTLR_nASSGIreq` is masked off in both the
  guest and the userspace write.
- Guest `GICD_CTLR` write: `nassgireq` is read-only only when the distributor
  was enabled and stays enabled; the write that enables or disables the
  distributor can change it.
- Userspace `GICD_CTLR` write: `vgic_mmio_uaccess_write_v3_misc()` stores
  `enabled` and `nassgireq` and does not call `vgic_v4_configure_vsgis()`.
- `vgic_v4_configure_vsgis()`: called from two places only,
  `vgic_mmio_write_v3_misc()` and `vgic_v3_map_resources()`; the second calls
  it only when `kvm_vgic_global_state.has_gicv4_1`, runs once, from
  `kvm_vgic_map_resources()` on first vCPU run, and applies a restored
  `nassgireq`.
- Host irqs: already allocated by `its_alloc_vcpu_sgis()` when
  `vgic_v4_init()` ran; `vgic_v4_enable_vsgis()` only looks them up with
  `irq_find_mapping()`.
- To hardware: enabled, group and priority through
  `vgic_v4_sync_sgi_config()` and `irq_domain_activate_irq()`, then pending.
- To hardware, pending: `irq_set_irqchip_state()` is called with
  `irq->pending_latch` whether set or not; a false latch sends the clearing
  VSGI.
- To software: pending only, read with `irq_get_irqchip_state()` into
  `irq->pending_latch` before `irq_domain_deactivate_irq()`.
- Active state: transferred in neither direction; `vgic_mmio_change_active()`
  forces `irq->active = false` for a hardware SGI.
- While hardware-backed: guest priority and group writes go through
  `its_prop_update_vsgi()`; enable writes go through `enable_irq()` in
  `vgic_mmio_write_senable()` and `disable_irq_nosync()` in
  `vgic_mmio_write_cenable()`, on `irq->host_irq`; both are in
  `arch/arm64/kvm/vgic/vgic-mmio.c`.
