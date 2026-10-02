- `kvm_dirty_ring_push()` publish step: `smp_wmb()` followed by a plain store
  of `KVM_DIRTY_GFN_F_DIRTY` in `kvm_dirty_gfn_set_dirtied()`; it does not use
  `smp_store_release()`.
- `smp_store_release()`: used only by `kvm_dirty_gfn_set_invalid()` on the
  reset side, after slot and offset have been read.
- `dirty_index` and `reset_index`: kernel-private in `struct kvm_dirty_ring`;
  the mapped pages hold only the `struct kvm_dirty_gfn` array, so `flags` is
  the whole handshake with userspace.
- `kvm_dirty_ring_reset()` and `kvm_reset_dirty_gfn()`: call no TLB flush
  themselves.
- TLB flush after reset: `kvm_vm_ioctl_reset_dirty_pages()` calls
  `kvm_flush_remote_tlbs()` once for all rings, after it drops `slots_lock`,
  and only when at least one entry was reset.
- `kvm_dirty_ring_reset()` signature: `(kvm, ring, int *nr_entries_reset)`;
  returns 0, or `-EINTR` when a signal is pending.
- `*nr_entries_reset`: one counter shared across all vCPUs of the ioctl; the
  walk stops when it reaches `INT_MAX`.
- `kvm_cpu_dirty_log_size()`: takes `struct kvm *`; weak default returning 0
  in `virt/kvm/dirty_ring.c`, x86 override in `arch/x86/kvm/mmu/mmu.c` returns
  `kvm->arch.cpu_dirty_log_size`.
