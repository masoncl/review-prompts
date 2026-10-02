- `kvm_timer_init_vm()`: runs twice for a GICv5 guest; `kvm_arch_init_vm()`
  stores bare numbers, then `kvm_vgic_create()` calls it again and stores
  typed IDs.
- `kvm_arm_timer_set_attr()`: not refused for GICv5; it stores any ID that
  passes `irq_is_ppi()`, so a bare 27 gets `-EINVAL` and a typed PPI is
  accepted.
- `timer_irqs_are_valid()`: fails if the ID of any of the vCPU's
  `nr_timers()` timers (two without NV) differs from `get_vgic_ppi()` of its
  default; `kvm_timer_enable()` then returns `-EINVAL` on first run.
- Directly injected timer: `kvm_timer_update_irq()` returns before
  `kvm_vgic_inject_irq()` for `direct_vtimer` and `direct_ptimer`; hardware
  raises the PPI through the bit in `vgic_ppi_dvir`.
- Physical active state at load: `kvm_timer_vcpu_load_gic()` sets it
  unconditionally for a GICv5 guest, whatever the pending state.
- Physical active state at put: `kvm_timer_vcpu_put()` clears it for the
  direct timers; other models do nothing there.
- Mechanism: on a GICv5 host the timer interrupts sit behind `timer_chip`;
  for a GICv5 guest `timer_irq_set_irqchip_state()` turns the active state
  of a forwarded interrupt into `irq_chip_mask_parent()` or
  `irq_chip_unmask_parent()`.
- GICv3 guest on a GICv5 host: `timer_irq_set_irqchip_state()` passes the
  active state to the parent instead.
