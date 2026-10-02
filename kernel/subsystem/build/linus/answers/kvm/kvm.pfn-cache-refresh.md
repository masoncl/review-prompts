- `gfn_to_pfn_cache_invalidate_start()`: only clears `gpc->valid`; it does not
  touch `mmu_invalidate_in_progress` or the invalidation range.
- `kvm_mmu_notifier_invalidate_range_start()`: raises
  `kvm->mn_active_invalidate_count` before it calls
  `gfn_to_pfn_cache_invalidate_start()`, and before `mmu_lock` is taken.
- `mmu_notifier_retry_cache()`: has no range test; any MMU notifier
  invalidation in flight on the VM, or any change of `mmu_invalidate_seq`,
  makes the refresh retry.
- `gfn_to_pfn_cache_invalidate_start()`: takes `gpc->lock` for read first and
  for write only on a match; it skips a cache whose `valid` is false.
- `hva_to_pfn_retry()`: clears `valid` before it drops the lock, so an
  invalidation during the refresh never touches the cache; only the recheck
  in `mmu_notifier_retry_cache()` catches it.
- `mmu_invalidate_seq`: bumped by `kvm_mmu_invalidate_end()`, which
  `kvm_handle_hva_range()` calls only when the range intersects a memslot;
  `mn_active_invalidate_count` is raised and lowered for every MMU notifier
  invalidation.
