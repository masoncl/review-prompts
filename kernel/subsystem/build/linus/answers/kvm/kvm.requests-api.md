- `smp_wmb()` in `__kvm_make_request()`: pairs only with
  `smp_mb__after_atomic()` in `kvm_check_request()`. `kvm_test_request()` and
  `kvm_request_pending()` contain no `smp_rmb()` or any other barrier.
- `kvm_make_all_cpus_request()` and `kvm_make_vcpu_request()`: no barrier call
  in either body. The barrier that orders the bit before the mode read is
  `smp_mb__before_atomic()` in `kvm_vcpu_exiting_guest_mode()`, reached
  through `kvm_request_needs_ipi()`.
- There is no kvm_make_all_cpus_request_except() here.
  `kvm_make_all_cpus_request()` and `kvm_make_vcpus_request_mask()` in
  `virt/kvm/kvm_main.c` are two separate loops over `kvm_make_vcpu_request()`.
- `kvm_make_vcpu_request()` after a successful `kvm_vcpu_wake_up()`: returns at
  once. `kvm_request_needs_ipi()` is not called, so the mode is not touched
  and that vCPU gets no IPI, with or without `KVM_REQUEST_WAIT`.
- IRQs: `smp_call_function_many()` is reached whenever the kick mask is not
  empty. `smp_call_function_many_cond()` in `kernel/smp.c` asserts IRQs
  enabled and task context whether or not `KVM_REQUEST_WAIT` is set.
