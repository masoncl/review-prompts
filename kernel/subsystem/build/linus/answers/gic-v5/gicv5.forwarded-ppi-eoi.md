- Marking: `irqd_set_forwarded_to_vcpu()` and `irqd_clr_forwarded_to_vcpu()`;
  the driver keeps no bitmap of its own.
- The flag lives in the shared `struct irq_common_data`, so every chip
  stacked on the PPI sees it through `irqd_is_forwarded_to_vcpu()`.
- `gicv5_ppi_irq_eoi()` on a forwarded PPI: returns without issuing any
  instruction; the priority drop was already issued in `gicv5_handle_irq()`.
- KVM timer PPIs on a GICv5 host: `kvm_irq_init()` in
  `arch/arm64/kvm/arch_timer.c` pushes its own chip on top when
  `kvm_vgic_global_state.type == VGIC_V5`.
- `irq_set_vcpu_affinity()` stops at the first chip from the top that has
  the callback, so for those PPIs `timer_irq_set_vcpu_affinity()` sets the
  flag, not `gicv5_ppi_irq_set_vcpu_affinity()`.
- `timer_irq_eoi()`: skips `irq_chip_eoi_parent()` when forwarded, so
  `gicv5_ppi_irq_eoi()` is not reached for them.
- The host does not deactivate a forwarded PPI from `irq_eoi`; KVM owns its
  active state, and how depends on the guest:

| Guest | What KVM does with the host PPI |
|---|---|
| GICv5 | `timer_irq_set_irqchip_state()` turns an `IRQCHIP_STATE_ACTIVE` request into `irq_chip_mask_parent()` or `irq_chip_unmask_parent()`: masked in `kvm_timer_vcpu_load_gic()`, unmasked in `kvm_timer_vcpu_put()`; the PPI is handed to the guest with the bit `vgic_v5_set_ppi_dvi()` sets |
| GICv3 on GICv5 | the request passes through to `gicv5_ppi_irq_set_irqchip_state()`; when KVM emulates the guest's deactivate, `vgic_v3_deactivate_phys()` issues CDDI itself |
