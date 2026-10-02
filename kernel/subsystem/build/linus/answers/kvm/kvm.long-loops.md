- Generic code: nothing under `virt/kvm/` yields `mmu_lock` itself;
  `kvm_handle_hva_range()`, `kvm_handle_gfn_range()` and the dirty-log loops
  never drop it mid-walk, only the arch handler they call may yield.
- `cond_resched_lock()`: not called on `mmu_lock` in any kvm directory; yield
  sites use `cond_resched_rwlock_write()` or `cond_resched_rwlock_read()`, or
  unlock fully.
- `may_block` in `struct kvm_gfn_range`: the arch walk yields only if it is
  set; aging passes false, `kvm_mmu_notifier_invalidate_range_start()` passes
  `mmu_notifier_range_blockable()`.
- `tdp_mmu_iter_cond_resched()`: does not call `tdp_iter_restart()`; it sets
  `iter->yielded`, and `tdp_iter_next()` restarts from the root.
- After `tdp_mmu_iter_cond_resched()` returns true the caller must
  `continue`; `tdp_mmu_iter_set_spte()` and `__tdp_mmu_set_spte_atomic()`
  warn if `iter->yielded` is set.
- `tdp_mmu_iter_need_resched()`: refuses to yield until
  `next_last_level_gfn` differs from `yielded_gfn`.
- Leaving a yield-safe root loop early: the caller must call
  `kvm_tdp_mmu_put_root()`, as `kvm_tdp_mmu_try_split_huge_pages()` does,
  unless it keeps the reference, as `kvm_tdp_mmu_alloc_root()` does.
- `tdp_mmu_split_huge_pages_root()`: unlocks fully to allocate, then sets
  `iter.yielded` itself.
- `__walk_slot_rmaps()`: yields only if `can_yield`; does not restart, the
  rmap iterator continues from its current gfn.
- `kvm_zap_obsolete_pages()`: yields without calling
  `kvm_mmu_commit_zap_page()`; it commits once after the loop, and restarts
  the list walk after a yield.
- `mmu_sync_children()`: re-walks from the parent after each yield.
- arm64 `stage2_apply_range()`: re-reads `mmu->pgt` for every chunk and
  returns if it is NULL, 0 if the lock was dropped and `-EINVAL` if not.
- arm64 `kvm_mmu_split_huge_pages()`: unlocks fully, then re-reads
  `kvm->arch.mmu.pgt`.
- **Potentially unsafe usage**: yielding `mmu_lock` with SPTEs zapped and
  not yet flushed.
  - Unsafe: for SPTEs zapped from a valid root for an invalidation; a second
    invalidation of the range finds nothing to zap, and
    `kvm_handle_hva_range()` flushes only if a handler returned true.
  - Safe: flush first, as `tdp_mmu_zap_leafs()` does by passing `flush` to
    `tdp_mmu_iter_cond_resched()`, and `__kvm_rmap_zap_gfn_range()` does with
    `flush_on_yield`.
  - Safe: shadow pages of an obsolete generation, after
    `__kvm_mmu_zap_all_fast_front_half()` requested
    `KVM_REQ_MMU_FREE_OBSOLETE_ROOTS` in the same lock hold, as
    `kvm_zap_obsolete_pages()` does.
  - Safe: SPTEs under an invalid TDP root; `tdp_mmu_zap_leafs()` sets `flush`
    only when `!root->role.invalid`.
  - Safe: write-protection for dirty logging, flushed after unlock under
    `slots_lock` with `kvm_flush_remote_tlbs_memslot()`, as
    `kvm_mmu_slot_apply_flags()` does.
  - Safe: a zap of everything for `kvm_arch_flush_shadow_all()`, which
    generic code calls from `kvm_mmu_notifier_release()`, as
    `kvm_mmu_zap_all()` and `kvm_tdp_mmu_zap_all()` do; the mm is exiting or
    the VM is being destroyed, and `kvm_vcpu_ioctl()` returns `-EIO` when
    `kvm->mm != current->mm`.
