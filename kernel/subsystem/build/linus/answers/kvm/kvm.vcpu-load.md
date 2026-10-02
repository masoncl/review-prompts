- `vcpu_load()` itself writes the per-CPU `kvm_running_vcpu` and registers
  the notifier; `vcpu->cpu` is written by arch code, for example x86 and
  arm64 `kvm_arch_vcpu_load()`.
- `kvm_sched_out()` and `kvm_sched_in()` clear and set `kvm_running_vcpu`
  too, so `kvm_get_running_vcpu()` is valid across a reschedule.
- Generic `kvm_vcpu_ioctl()` never calls `vcpu_load()` for a handler;
  `kvm_vcpu_pre_fault_memory()` loads for itself.
- x86: `kvm_arch_vcpu_ioctl()` loads once around its whole switch; the
  handlers that `kvm_vcpu_ioctl()` calls directly load one by one, and
  `kvm_arch_vcpu_ioctl_get_regs()` and `kvm_arch_vcpu_ioctl_get_sregs()` are
  in `arch/x86/kvm/regs.c`.
- arm64 and riscv: `vcpu_load()` is called only in
  `kvm_arch_vcpu_ioctl_run()`; other vCPU ioctl handlers run unloaded.
- `preempt_notifier_register()` in `kernel/sched/core.c`: an unconditional
  `hlist_add_head()` onto `current->preempt_notifiers`, so a second
  `vcpu_load()` before `vcpu_put()` links the same node twice.
- **Potentially unsafe usage**: `vcpu_load()` without holding `vcpu->mutex`.
  - Unsafe: on a vCPU another task can reach; `struct kvm_vcpu` has a single
    `preempt_notifier` and `vcpu_load()` checks nothing.
  - Safe: on a vCPU no other task can reach: before it is in
    `kvm->vcpu_array`, as x86 `kvm_arch_vcpu_create()` does, or while it is
    destroyed, as `nested_vmx_free_vcpu()` does;
    `kvm_lockdep_assert_vcpu_is_locked_or_unreachable()` defines the
    condition.
  - Safe: outside the locked part of `kvm_vcpu_ioctl()` when the caller takes
    `vcpu->mutex` itself, as x86 `kvm_arch_vcpu_postcreate()` and
    `tdx_vcpu_unlocked_ioctl()` do.
