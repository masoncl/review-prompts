- `kvm->lock`, `vcpu->mutex` and `slots_lock` are the three that
  `Documentation/virt/kvm/locking.rst` names; `slots_arch_lock` is not,
  `kvm_swap_active_memslots()` unlocks it before the wait.
- Direct waits on `kvm->srcu` in `virt/kvm/kvm_main.c` are under `slots_lock`:
  `kvm_swap_active_memslots()` and `kvm_io_bus_unregister_dev()`.
- `kvm->lock` and `vcpu->mutex`: reach the wait by nesting `slots_lock`
  inside; for example `KVM_CREATE_IRQCHIP` in `arch/x86/kvm/x86.c` calls
  `kvm_pic_destroy()` under `kvm->lock` on its error path.
- `kvm_vm_ioctl_set_msr_filter()` in `arch/x86/kvm/msrs.c`: drops `kvm->lock`
  before `synchronize_srcu()`.
- **Potentially unsafe usage**: taking `kvm->lock`, `vcpu->mutex` or
  `slots_lock` while in a `kvm->srcu` read side section.
  - Unsafe: with a call that waits for the mutex; the mutex holder waits for
    the reader in `synchronize_srcu_expedited()`, and the reader waits for the
    mutex.
  - Safe: leave the read side first, as `kvm_inhibit_apic_access_page()` in
    `arch/x86/kvm/lapic.c` does: `kvm_vcpu_srcu_read_unlock()`, take
    `slots_lock`, recheck `apic_access_memslot_enabled` under it, unlock,
    `kvm_vcpu_srcu_read_lock()`.
  - Safe: `mutex_trylock()`, which never waits, as
    `kvm_s390_try_set_tod_clock()` does on `kvm->lock` for
    `handle_set_clock()`; on failure the instruction is retried.
  - Safe: `slots_arch_lock` inside the read side, as
    `kvm_s390_vm_set_migration()` in `arch/s390/kvm/s390/s390.c` does;
    `kvm_swap_active_memslots()` unlocks it before
    `synchronize_srcu_expedited()`.
