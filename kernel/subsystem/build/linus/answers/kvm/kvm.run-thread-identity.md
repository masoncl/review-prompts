- `vcpu->pid` is not RCU-protected; the store is under
  `write_lock(&vcpu->pid_lock)` and there is no `synchronize_rcu()`.
- `kvm_vcpu_yield_to()`: uses `read_trylock()` and returns 0 when the lock is
  contended; it does not wait.
- `kvm_arch_vcpu_run_pid_change()`: called before the new pid is taken; on
  error `vcpu->pid` is left unchanged, so the next `KVM_RUN` calls it again.
- `kvm_arch_vcpu_run_pid_change()`: a stub that returns 0 without
  `CONFIG_HAVE_KVM_VCPU_RUN_PID_CHANGE`, which only arm64 selects.
- `vcpu->pid` is `NULL` from `kvm_vcpu_init()` until the first `KVM_RUN`.
- **Potentially unsafe usage**: reading `vcpu->pid` without
  `vcpu->pid_lock`.
  - Unsafe: from a task that does not hold `vcpu->mutex`, while a vCPU fd
    still exists; `KVM_RUN` can replace the pointer and `put_pid()` the old
    one.
  - Safe: while holding `vcpu->mutex`, which the only writer, the `KVM_RUN`
    case, holds, as the compare in the `KVM_RUN` case and arm64
    `kvm_arch_vcpu_load()` do.
  - Safe: in `kvm_vcpu_destroy()`, reached only from `kvm_destroy_vcpus()`
    when no vCPU fd is left to issue `KVM_RUN`; each vCPU fd holds a VM
    reference until `kvm_vcpu_release()`.
