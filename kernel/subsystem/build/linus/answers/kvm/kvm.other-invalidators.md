- There is no kvm_gmem_invalidate_begin() here; guest_memfd uses
  `kvm_gmem_invalidate_start()` and `__kvm_gmem_invalidate_start()` in
  `virt/kvm/guest_memfd.c`.
- `kvm_mmu_invalidate_end()` asserts three things: the write lock,
  `KVM_BUG_ON()` if the count is negative after the decrement, and
  `WARN_ON_ONCE(kvm->mmu_invalidate_range_start == INVALID_GPA)`.
- `kvm_mmu_invalidate_end()` has no check that the count was non-zero before
  the decrement, other than the negative test.
- No-range warning: masked while another invalidation overlaps, since the
  range is reset only on the 0 to 1 start.
- Range before first unlock: after `kvm_mmu_invalidate_start()`, call
  `kvm_mmu_invalidate_range_add()` before `mmu_lock` is dropped; a fault that
  takes the lock in between finds the count non-zero and the range still
  `INVALID_GPA`, which `mmu_invalidate_retry_gfn()` warns about, see "Retry
  helpers".
- Zap inside the window: x86 `kvm_unmap_gfn_range()` asserts
  `mmu_invalidate_in_progress` non-zero or `slots_lock` held.
- Both or neither: where start and end are each conditional on finding a
  slot or binding, that set must not change between them.
  - guest_memfd: `filemap_invalidate_lock()` or
    `filemap_invalidate_lock_shared()` held across both.
  - `kvm_vm_set_mem_attributes()`: `slots_lock` held across both.
- `__kvm_gmem_invalidate_start()`: unlocks `mmu_lock` before returning;
  `__kvm_gmem_invalidate_end()` retakes it; in `kvm_gmem_punch_hole()` the
  truncate runs in between.
- `kvm_gmem_release()` and `kvm_gmem_error_folio()`: also bracket with
  start and end; neither truncates.
- `kvm_zap_gfn_range()` in `arch/x86/kvm/mmu/mmu.c`: start, add, zap, flush,
  end under one `write_lock()`, but both zap helpers are called with yielding
  allowed, so the lock can be dropped inside the window.
- `mmu_invalidate_seq` is also incremented directly, with no start/end pair,
  under `mmu_lock`: for example `invalidate_vncr_va()` in
  `arch/arm64/kvm/nested.c` and `kvmppc_radix_flush_memslot()`.
