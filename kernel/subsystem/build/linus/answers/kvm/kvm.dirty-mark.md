- Both `WARN_ON_ONCE()` checks: compiled under `CONFIG_HAVE_KVM_DIRTY_RING`
  and do not test `kvm->dirty_ring_size`, so they can also fire on a VM that
  uses only the bitmap.
- No-vCPU warning: also skipped when `refcount_read(&kvm->users_count)` is 0.
- `kvm_arch_allow_write_without_running_vcpu()`: arm64 is the only override
  (`arch/arm64/kvm/vgic/vgic-its.c`); x86 has none and gets the
  `return false` version in `virt/kvm/dirty_ring.c`.
- The hook only silences the warning; it has no part in choosing ring or
  bitmap.
- arm64 window: `table_write_in_progress` is set around every
  `vgic_write_guest_lock()` call (`arch/arm64/kvm/vgic/vgic.h`), which covers
  ITS table writes, `vgic_v3_save_pending_tables()` and
  `vgic_v3_lpi_sync_pending_status()`.
- Gate for recording: `memslot && kvm_slot_dirty_track_enabled(memslot)`, the
  `KVM_MEM_LOG_DIRTY_PAGES` flag, not `memslot->dirty_bitmap`.
- `memslot->dirty_bitmap` is tested only after `kvm->dirty_ring_size && vcpu`
  fails; a slot that turns logging on in ring-only mode gets no bitmap from
  `kvm_prepare_memory_region()`.
- **Potentially unsafe usage**: calling `mark_page_dirty_in_slot()`,
  `mark_page_dirty()` or `kvm_write_guest()` with no running vCPU.
  - Unsafe: under `CONFIG_HAVE_KVM_DIRTY_RING`, when the hook returns false
    and `users_count` is non-zero; the `WARN_ON_ONCE()` in
    `mark_page_dirty_in_slot()` fires, and with a ring and no bitmap the write
    is not recorded.
  - Safe: inside the window the hook reports, on a VM with
    `kvm->dirty_ring_with_bitmap` set or no ring, as `vgic_write_guest_lock()`
    does; the bit goes to the bitmap.
  - Safe: on an architecture that does not select
    `CONFIG_HAVE_KVM_DIRTY_RING`, as s390 `adapter_indicators_set()` does; the
    `WARN_ON_ONCE()` in `mark_page_dirty_in_slot()` is compiled out and the
    bit goes to the bitmap.
