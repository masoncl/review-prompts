- x86 `IN_GUEST_MODE` write: `vcpu_enter_guest()` in `arch/x86/kvm/x86.c` uses
  `smp_store_release()`, then `kvm_vcpu_srcu_read_unlock()`, then
  `smp_mb__after_srcu_read_unlock()`. x86 does not use `smp_store_mb()` here.
- Full barrier before the x86 read of requests: the `smp_mb()` in
  `__srcu_read_unlock()` in `kernel/rcu/srcutree.c`, reached through
  `kvm_vcpu_srcu_read_unlock()`; `smp_mb__after_srcu_read_unlock()` is an
  empty inline.
- Other architectures: the full barrier after the `IN_GUEST_MODE` store is not
  always `smp_store_mb()`. For example `kvmppc_prepare_to_enter()` does a
  plain store then `smp_mb()`, and riscv a plain store then
  `kvm_vcpu_srcu_read_unlock()` and `smp_mb__after_srcu_read_unlock()`. Search
  for `IN_GUEST_MODE`.
- x86 `OUTSIDE_GUEST_MODE` write in `vcpu_enter_guest()`: a plain store
  followed by `smp_wmb()`, with IRQs still disabled, both after VM-exit and on
  the cancelled entry.
- `walk_shadow_page_lockless_end()`, when `is_tdp_mmu_active()` is false:
  writes `OUTSIDE_GUEST_MODE`, not `IN_GUEST_MODE`.
- `IN_GUEST_MODE` to `EXITING_GUEST_MODE` has a second writer:
  `__kvm_vcpu_kick()` uses `WRITE_ONCE()`, with no `cmpxchg()` and no
  `smp_mb__before_atomic()`, when the target is this CPU's `kvm_running_vcpu`.
- `kvm_running_vcpu`: set from `vcpu_load()` or `kvm_sched_in()` until
  `vcpu_put()` or `kvm_sched_out()`, so that branch also covers a kick from an
  interrupt handler that interrupted the vCPU thread.
- `kvm_arch_vcpu_should_kick()` on mips and powerpc: returns 1 and does not
  call `kvm_vcpu_exiting_guest_mode()`, so `__kvm_vcpu_kick()` there moves the
  mode only in the `kvm_running_vcpu` branch.
