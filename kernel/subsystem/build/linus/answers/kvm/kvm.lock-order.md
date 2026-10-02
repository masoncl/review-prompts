- Global chain, outer to inner: `kvm_usage_lock` → `cpus_read_lock()` →
  `kvm_lock`.
- `kvm->lock` is outside `vcpu->mutex`, not the reverse.
- `kvm_enable_virtualization()` in `virt/kvm/kvm_main.c`: holds
  `kvm_usage_lock` across `cpuhp_setup_state()`; `__cpuhp_setup_state()` in
  `kernel/cpu.c` takes `cpus_read_lock()`.
- `kvm_usage_lock`: static in `virt/kvm/kvm_main.c`, defined only under
  `CONFIG_KVM_GENERIC_HARDWARE_ENABLING`; `kvm_suspend()` and `kvm_resume()`
  assert it is not held.
- `kvm_lock_all_vcpus()` and `kvm_trylock_all_vcpus()`: assert `kvm->lock` and
  take each `vcpu->mutex` with `kvm->lock` as nest lock.
- `kvm_create_vm()`: only initialises the mutexes; there is no lockdep priming
  of the chain there or elsewhere in the kvm directories.
- `kvm_swap_active_memslots()`: has no assertion on `slots_arch_lock`; it only
  unlocks it. `kvm_set_memslot()` takes it, inside `slots_lock`.
