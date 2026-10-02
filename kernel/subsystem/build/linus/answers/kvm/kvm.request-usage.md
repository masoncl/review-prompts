- `kvm_make_request()`: a `BUILD_BUG_ON()`, not a run-time warning. The build
  fails unless the request is a compile-time constant without
  `KVM_REQUEST_NO_ACTION`.
- Run-time request number: use `__kvm_make_request()`, as
  `kvm_make_vcpu_request()` and `kvm_s390_sync_request()` do.
- `KVM_REQ_VM_DEAD`: `kvm_check_request()` and `kvm_clear_request()` each have
  a `BUILD_BUG_ON()` against it. Test it with `kvm_test_request()`, as
  `vcpu_enter_guest()` does; the bit is never cleared.
- Requests with no `kvm_check_request()` exist on purpose. x86
  `KVM_REQ_MCLOCK_INPROGRESS` is made by
  `kvm_make_mclock_inprogress_request()` and cleared by the sender's thread
  with `kvm_clear_request()` in `kvm_end_pvclock_update()`; while set it keeps
  vCPUs out of the guest.
- `kvm_make_request_and_kick()`: request plus kick in one call; not defined
  under `CONFIG_S390`.
- Blocked target: a wake-up alone does not unblock. `kvm_vcpu_block()` sleeps
  again unless `kvm_vcpu_check_block()` finds `kvm_arch_vcpu_runnable()`, a
  pending timer, a signal or `KVM_REQ_UNBLOCK`.
- `kvm_arch_vcpu_runnable()` differs by architecture: powerpc's tests
  `kvm_request_pending()`; x86's tests only the requests named in
  `kvm_vcpu_has_events()` and in `kvm_is_exception_pending()`; arm64's tests
  no request.
- Direct access to `requests`: nothing outside the helpers in
  `include/linux/kvm_host.h` writes it. The only direct reads are the
  tracepoints in `arch/x86/kvm/trace.h` and `arch/powerpc/kvm/trace.h`.
- **Potentially unsafe usage**: making a request and then reading `vcpu->mode`
  directly to decide whether to notify the target.
  - Unsafe: with no full barrier between `kvm_make_request()` and the read.
    The `smp_wmb()` does not order the store to `requests` against the load of
    `vcpu->mode`, so the entry check in `vcpu_enter_guest()` can miss the
    request while the sender sees a mode other than `IN_GUEST_MODE`.
  - Safe: through `kvm_vcpu_kick()` or `kvm_make_all_cpus_request()`, where
    `kvm_vcpu_exiting_guest_mode()` supplies `smp_mb__before_atomic()`.
  - Safe: with `smp_mb__after_atomic()` between the two, as
    `vmx_deliver_nested_posted_interrupt()` in `arch/x86/kvm/vmx/vmx.c` does
    before `kvm_vcpu_trigger_posted_interrupt()`.
