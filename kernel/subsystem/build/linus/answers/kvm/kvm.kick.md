- `wait` true: the IPI is `smp_call_function_single(cpu, ack_kick, NULL,
  wait)`; `wait` false: `smp_send_reschedule(cpu)`.
- `wait` true needs IRQs enabled and task context:
  `__smp_call_function_single()` in `kernel/smp.c` has a `WARN_ON_ONCE()` for
  each. `kvm_vcpu_kick()` may be called with IRQs disabled.
- Where `kvm_arch_vcpu_should_kick()` calls `kvm_vcpu_exiting_guest_mode()`:
  `wait` is acted on only when this call's `cmpxchg()` saw `IN_GUEST_MODE` and
  `vcpu->cpu` is another online CPU. A target already in
  `EXITING_GUEST_MODE` or in `READING_SHADOW_PAGE_TABLES` gets no IPI, and the
  call returns without waiting.
- Guarantee: a kick guarantees only that the target is on its way out. To know
  it has left, use a `KVM_REQUEST_WAIT` request through
  `kvm_make_all_cpus_request()`; see the comment above
  `KVM_REQ_OUTSIDE_GUEST_MODE` in `include/linux/kvm_host.h`.
- Target is this CPU's `kvm_running_vcpu`: no IPI, and `wait` is ignored; the
  only effect is the mode write described under "vCPU mode".
- That mode write is read back by x86 `kvm_vcpu_exit_request()`, which tests
  for `EXITING_GUEST_MODE`. arm64's `kvm_vcpu_exit_request()` does not read
  `vcpu->mode`.
- mips and powerpc: `kvm_arch_vcpu_should_kick()` returns 1, so every target
  that is not blocked and last ran on another online CPU gets an IPI,
  whatever its mode.
- `CONFIG_S390`: `__kvm_vcpu_kick()`, `kvm_vcpu_kick()` and
  `kvm_make_request_and_kick()` are not built. s390 uses
  `kvm_s390_sync_request()` and `exit_sie()` in `arch/s390/kvm/s390/s390.c`.
