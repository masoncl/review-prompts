- Distributor registration: `vgic_register_dist_iodev()` runs with
  `kvm->slots_lock` held and `kvm->arch.config_lock` dropped; the caller's
  `vcpu->mutex` is held too. `config_lock` is dropped after
  `dist->vgic_dist_base` has been copied to a local.
- There is no vgic_ready() accessor in this tree; `dist->ready` is read
  directly, and only inside `kvm_vgic_map_resources()`.
- Reads of `dist->ready`: `smp_load_acquire()` with no lock on the fast path,
  then a plain read under both locks.
- Publication: `smp_store_release(&dist->ready, true)` after the distributor
  frame is registered, with `slots_lock` held and `config_lock` already
  dropped.
- GICv5: `vgic_v5_map_resources()` registers no distributor frame; `ready` is
  still set.
- Clearing: `kvm_vgic_dist_destroy()` stores `false` with a plain store under
  `config_lock`.
- Failure: every non-zero return ends in `kvm_vm_dead()`. That includes
  userspace configuration errors such as `-ENXIO` for an unset base and
  `-EBUSY` for an uninitialised GICv3.
- Failure does not call `kvm_vgic_destroy()`; nothing already registered is
  unregistered and `ready` stays false. Teardown happens only in
  `kvm_arch_destroy_vm()`.
- After `kvm_vm_dead()`: VM, vCPU and device ioctls return `-EIO`; see the
  `vm_dead` tests in `virt/kvm/kvm_main.c`.
