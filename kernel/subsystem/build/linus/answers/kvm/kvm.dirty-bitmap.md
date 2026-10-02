- `kvm_get_dirty_log_protect()` and `kvm_clear_dirty_log_protect()`: static,
  built only with `CONFIG_KVM_GENERIC_DIRTYLOG_READ_PROTECT`.
- Without that option: `kvm_get_dirty_log()` is built instead; it copies the
  live bitmap and neither clears nor protects, and `KVM_CLEAR_DIRTY_LOG` is
  not handled.
- Kerneldoc above `kvm_get_dirty_log_protect()` and
  `kvm_vm_ioctl_get_dirty_log()`: lists "copy to userspace, then caller
  flushes"; the code flushes inside `kvm_get_dirty_log_protect()` before
  `copy_to_user()`, and the caller flushes nothing.
- TLB flush locking: runs after `KVM_MMU_UNLOCK()` in both GET and CLEAR, in
  generic code; `kvm_flush_remote_tlbs_memslot()` asserts `kvm->slots_lock`.
- `KVM_MMU_LOCK()`: `write_lock()` only where the arch defines
  `KVM_HAVE_MMU_RWLOCK`, otherwise `spin_lock()`; see `virt/kvm/kvm_mm.h`.
- GET with `kvm->manual_dirty_log_protect`: copies the live bitmap as is;
  clears no bit, takes no `mmu_lock`, never touches the second half.
- GET without manual protect: clears each non-zero word with `xchg()`, not an
  atomic_long helper.
- `kvm_alloc_dirty_bitmap()`: `__vcalloc(2, dirty_bytes, GFP_KERNEL_ACCOUNT)`.
- Second half outside generic code: x86 does not use it;
  `kvm_vm_ioctl_get_dirty_log_hv()` in `arch/powerpc/kvm/book3s_hv.c` uses it
  as its output buffer, by open-coded pointer arithmetic rather than
  `kvm_second_dirty_bitmap()`.
