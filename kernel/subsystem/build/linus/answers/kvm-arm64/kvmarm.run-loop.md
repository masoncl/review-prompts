- Order before entry: `kvm_xfer_to_guest_mode_handle_work()`,
  `check_vcpu_requests()`, `preempt_disable()`, `kvm_nested_flush_hwstate()`,
  `kvm_pmu_flush_hwstate()` (if `kvm_vcpu_has_pmu()`), `local_irq_disable()`,
  `kvm_vgic_flush_hwstate()`, `kvm_pmu_update_vcpu_events()`,
  `smp_store_mb(vcpu->mode, IN_GUEST_MODE)`, last check,
  `kvm_arch_vcpu_ctxflush_fp()`.
- Timer: the loop has no timer flush; there is no kvm_timer_flush_hwstate()
  in this tree.
- `kvm_arm_vmid_update()`: not called in the loop; its only caller is
  `kvm_arch_vcpu_load()`.
- Nested and PMU flush: run with preemption off and IRQs on.
- `kvm_vgic_flush_hwstate()` in nested state: raises
  `KVM_REQ_GUEST_HYP_IRQ_PENDING` if `kvm_vgic_vcpu_pending_irq()`, calls
  `vgic_v3_flush_nested()` and returns.
- vgic flush before the last check: the request it raises is seen by
  `kvm_request_pending()` in `kvm_vcpu_exit_request()`, which abandons the
  entry so the next pass injects the IRQ.
- Last check: `ret <= 0 || kvm_vcpu_exit_request()`; it tests a userspace
  irqchip level change, `vcpu_on_unsupported_cpu()`, `kvm_request_pending()`
  and `xfer_to_guest_mode_work_pending()`.
- Signals: handled by `kvm_xfer_to_guest_mode_handle_work()` at the top of
  the next pass, not at the last check.
- Order after exit, all with IRQs off: `kvm_pmu_sync_hwstate()` (if
  `kvm_vcpu_has_pmu()`), `kvm_vgic_sync_hwstate()`, `kvm_timer_sync_user()`
  (userspace irqchip only), `kvm_timer_sync_nested()` (if `is_hyp_ctxt()`),
  `kvm_arch_vcpu_ctxsync_fp()`.
- `kvm_arch_vcpu_ctxsync_fp()`: warns unless IRQs are off.
- `kvm_nested_sync_hwstate()`: runs after `local_irq_enable()` and
  `handle_exit_early()`, before `preempt_enable()`.
- Abandoned entry, in order: `vcpu->mode = OUTSIDE_GUEST_MODE`, `isb()`,
  `kvm_pmu_sync_hwstate()` (if `kvm_vcpu_has_pmu()`), `kvm_timer_sync_user()`
  (userspace irqchip only), `kvm_vgic_sync_hwstate()`, `local_irq_enable()`,
  `preempt_enable()`, `continue`.
- Abandoned entry does not call `kvm_nested_sync_hwstate()`,
  `kvm_timer_sync_nested()` or `kvm_arch_vcpu_ctxsync_fp()`.
