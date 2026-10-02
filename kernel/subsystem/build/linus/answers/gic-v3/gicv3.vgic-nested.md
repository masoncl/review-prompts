- `vgic_state_is_nested()`: true when `is_nested_ctxt()` and the virtual
  `HCR_EL2` has `HCR_IMO` or `HCR_FMO` set (`WARN_ONCE()` if only one of
  them); it does not look at `ICH_HCR_EL2`.
- LR load point: `vgic_v3_load_nested()` writes the shadow LRs to hardware
  once, at vCPU load; they stay there across entries until
  `vgic_v3_put_nested()` zeroes them.
- On each entry: the only hardware write `kvm_vgic_flush_hwstate()` makes is
  in `vgic_v3_flush_nested()`, which writes L1's in-memory `ICH_HCR_EL2` OR
  `vgic_ich_hcr_trap_bits()` to hardware.
- Shadow `vgic_hcr`: the raw L1 value, nothing masked or merged in
  `vgic_v3_create_shadow_state()`.
- Compaction: `vgic_v3_create_shadow_lr()` skips L1 LRs with no
  `ICH_LR_STATE` and packs the rest from hardware index 0, so a hardware
  index is not the L1 index; convert with `lr_map_idx_to_shadow_idx()`.
- Translation: done by `translate_lr_pintid()`, with `vgic_get_vcpu_irq()`
  only; there is no lr_map_vintid() here.
- `translate_lr_pintid()` clears `ICH_LR_HW` when the lookup finds no irq,
  the irq is not `hw`, or `irq->intid > VGIC_MAX_SPI`; it does not set
  `ICH_LR_EOI`.
- `translate_lr_pintid()` overwrites the pINTID field with `irq->hwintid`
  whenever the lookup finds an irq, including when it has just cleared
  `ICH_LR_HW`.
- Write-back on every exit: `vgic_v3_sync_nested()`, called from
  `kvm_vgic_sync_hwstate()`, reads the hardware LRs and merges only
  `ICH_LR_STATE` into L1's in-memory LRs (`ICH_LR0_EL2` onwards); it also
  copies back `ICH_VMCR_EL2` and the EOIcount field of `ICH_HCR_EL2`.
- Write-back on put: `vgic_v3_put_nested()` copies back only the APRs; it
  does not call `vgic_v3_sync_nested()` or
  `vgic_v3_handle_nested_maint_irq()`.
