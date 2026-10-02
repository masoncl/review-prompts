- `KVM_REQ_VGIC_PROCESS_UPDATE`: handled in `check_vcpu_requests()` by
  `kvm_vgic_process_async_update()`, right after `KVM_REQ_IRQ_PENDING` is
  cleared.
- `check_nested_vcpu_requests()`: handles exactly `KVM_REQ_NESTED_S2_UNMAP`,
  `KVM_REQ_MAP_L1_VNCR_EL2` and `KVM_REQ_GUEST_HYP_IRQ_PENDING`; every other
  arm64 request is handled in `check_vcpu_requests()`.
- `KVM_REQ_GUEST_HYP_IRQ_PENDING`: calls `kvm_inject_nested_irq()`; it is
  last because the injection may do a put/load.
- `check_nested_vcpu_requests()`: called from the end of
  `check_vcpu_requests()`, so only when `kvm_request_pending()` was true and
  no earlier branch returned.
- `KVM_REQ_SUSPEND`: `check_vcpu_requests()` returns the value of
  `kvm_vcpu_suspend()` directly, so a pass that handles it skips
  `kvm_dirty_ring_check_request()` and `check_nested_vcpu_requests()`.
- A request still pending after `check_vcpu_requests()` returns 1: the last
  check abandons the entry and the loop runs `check_vcpu_requests()` again.
