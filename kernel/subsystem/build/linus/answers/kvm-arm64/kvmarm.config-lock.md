- Order, outermost first: `kvm->lock`, `vcpu->mutex`, `kvm->slots_lock`,
  `kvm->srcu` read side, `kvm->arch.config_lock`, then `its->cmd_lock` and
  `its->its_lock`.
- Where written down: the comment at the top of
  `arch/arm64/kvm/vgic/vgic.c` gives two chains, one from `kvm->lock` and one
  that reads `kvm->slots_lock`, `kvm->srcu`, `kvm->arch.config_lock`.
- Lockdep priming, both under `CONFIG_LOCKDEP`: `kvm_arch_init_vm()` takes
  `kvm->lock` then `config_lock`; `kvm_arch_vcpu_create()` takes
  `vcpu->mutex` then `config_lock`.
- `kvm->slots_lock` and `kvm->srcu`: nothing primes them against
  `config_lock`; lockdep learns that order only from real paths.
- `kvm_vgic_create()`: does no priming; it asserts `kvm->lock`, which the
  caller took, and uses `kvm_trylock_all_vcpus()`, returning `-EBUSY`.
  arm64 has no caller of `kvm_lock_all_vcpus()`.
- Protected state: find it with a search for
  `lockdep_assert_held(&kvm->arch.config_lock)` and for the lock name; it
  includes `kvm->arch.mpidr_data`, `kvm->arch.sysreg_masks`, the pKVM
  `is_created` state and `VCPU_PKVM_FINALIZED`.
- Not protected by it: bits of `kvm->arch.flags` set in
  `kvm_vm_ioctl_enable_cap()`, and the counter offset, which
  `kvm_vm_ioctl_set_counter_offset()` writes under `kvm->lock` plus all vCPU
  mutexes.
- `config_lock` inside an SRCU read side: `kvm_handle_guest_abort()` holds
  `kvm->srcu` around `io_mem_abort()`, and `vgic_mmio_write_v3_misc()` takes
  `config_lock`.
- **Unsafe usage**: waiting for a `kvm->srcu` grace period while holding
  `kvm->arch.config_lock`; `kvm_io_bus_unregister_dev()` calls
  `synchronize_srcu_expedited()`.
  - Safe: drop `config_lock` and keep `kvm->slots_lock`, as
    `kvm_vgic_destroy()` does before `vgic_unregister_redist_iodev()`.
  - Safe: `kvm_io_bus_register_dev()` under `config_lock`, as
    `vgic_v2_map_resources()` does; it uses `call_srcu()` and does not wait.
- Path with three locks: first run holds `vcpu->mutex`, then
  `kvm_vgic_map_resources()` takes `kvm->slots_lock` and `config_lock`.
- Path with `kvm->lock`, all vCPU mutexes and `config_lock`:
  `KVM_DEV_ARM_VGIC_SAVE_PENDING_TABLES` in `vgic_set_common_attr()`.
  `KVM_DEV_ARM_VGIC_CTRL_INIT` takes only `config_lock`.
