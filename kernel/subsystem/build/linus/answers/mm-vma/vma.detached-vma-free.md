- `vm_area_free()` in `mm/vma_init.c`: calls `kmem_cache_free()` at once. No
  `call_rcu()` is used for a VMA; only `SLAB_TYPESAFE_BY_RCU` on
  `vm_area_cachep` delays reuse of the memory by other types.
- `vma_mark_detached()`: waits for reader references, not for an RCU grace
  period; a reader may still hold the pointer after the free.
- `vm_area_cachep` has no constructor. `vm_refcnt` is written to 0 on every
  allocation: `vm_area_alloc()` through the `memset()` in `vma_init()`,
  `vm_area_dup()` through `vma_lock_init(new, true)`.
- That write loses no reader's increment: `vm_area_free()` asserts with
  `vma_assert_detached()` that the count is already 0, and
  `__refcount_inc_not_zero_limited_acquire()` does not raise a count of 0.
- `vm_freeptr`: the allocator's free pointer shares a union with `vm_start` and
  `vm_end` (`freeptr_offset` in `vma_state_init()`), so a free can overwrite
  only that union and not `vm_refcnt`, `vm_mm` or `vm_lock_seq`.
- **Potentially unsafe usage**: reading fields of a VMA found under RCU without
  a VMA read lock.
  - Unsafe: when the values are acted on with no later check that the mm was
    not write-locked meanwhile; the object may be freed or belong to another
    mapping.
  - Safe: take the lock first and recheck, as `lock_vma_under_rcu()` does.
  - Safe: bracket the reads with `mmap_lock_speculate_try_begin()` and
    `mmap_lock_speculate_retry()` and discard the result on retry, as
    `find_active_uprobe_speculative()` in `kernel/events/uprobes.c` does;
    `mmap_write_lock()` changes `mm_lock_seq` through
    `mm_lock_seqcount_begin()`.
