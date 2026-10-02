- Config symbol: there is no CONFIG_HAVE_KVM_DIRTY_RING_WITH_BITMAP here;
  `CONFIG_NEED_KVM_DIRTY_RING_WITH_BITMAP` in `virt/kvm/Kconfig` is the one,
  selected only by arm64.
- Writes that reach the bitmap: every `mark_page_dirty_in_slot()` call with no
  running vCPU on a logging slot, whether or not
  `kvm_arch_allow_write_without_running_vcpu()` returns true.
- `kvm_use_dirty_bitmap()` without `CONFIG_HAVE_KVM_DIRTY_RING`: an inline
  stub in `include/linux/kvm_dirty_ring.h` that returns `true` and asserts no
  lock.
- `kvm_prepare_memory_region()`: reuses `old->dirty_bitmap` before it asks
  `kvm_use_dirty_bitmap()`; there the helper decides only a fresh allocation.
