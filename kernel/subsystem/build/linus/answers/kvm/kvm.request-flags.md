- `KVM_REQUEST_NO_ACTION`: `kvm_make_vcpu_request()` does not call
  `__kvm_make_request()`, so no bit is set in `requests`. Only the wake-up and
  the IPI remain.
- `kvm_make_request_and_kick()` in `include/linux/kvm_host.h`: a third path
  that reads the flags, besides `kvm_make_all_cpus_request()` and
  `kvm_make_vcpus_request_mask()`. It calls `kvm_make_request()` and then
  `__kvm_vcpu_kick(vcpu, req & KVM_REQUEST_WAIT)`.
- `KVM_REQUEST_NO_WAKEUP` through `kvm_make_request_and_kick()`: ignored;
  `__kvm_vcpu_kick()` calls `kvm_vcpu_wake_up()` unconditionally.
- `KVM_REQUEST_WAIT` through `kvm_make_request_and_kick()`: weaker than through
  `kvm_make_all_cpus_request()`. Where `kvm_arch_vcpu_should_kick()` calls
  `kvm_vcpu_exiting_guest_mode()`, a target already in `EXITING_GUEST_MODE`
  or in `READING_SHADOW_PAGE_TABLES` gets no IPI and is not waited for; see
  "Kicks and wakeups".
- `KVM_REQ_OUTSIDE_GUEST_MODE` on x86: it sets no bit in `requests`, so the
  `EXITING_GUEST_MODE` test in `kvm_vcpu_exit_request()` is what ends the
  IRQs-off re-entry loop in `vcpu_enter_guest()`. The sender stays blocked
  until the target leaves that loop; see the comment in
  `tdx_exit_handlers_fastpath()`.
