- zap_page_range_single, zap_page_range_single_batched, zap_vma_ptes,
  unmap_page_range and unmap_single_vma are not in this tree. The functions
  are these, all in `mm/memory.c`:

| Function | Use | Caller must already have |
|---|---|---|
| `zap_vma_range()` | range within one VMA, NULL details | VMA kept alive by the caller, for example by the mmap lock or a VMA read lock; no lock is asserted. Not exported |
| `zap_vma_range_batched()` | same, caller's gather and details | gather started on `vma->vm_mm`; it does the notifier and `update_hiwater_rss()` itself. `unmap_mapping_range_tree()` calls it under `i_mmap_rwsem` only |
| `zap_special_vma_range()` | drivers; `EXPORT_SYMBOL_GPL` | nothing checked by caller: silently does nothing unless the range is inside the VMA and the VMA has `VM_PFNMAP` or `VM_MIXEDMAP` |
| `zap_vma_for_reaping()` | OOM reaper, whole VMA | mmap read lock; non-hugetlb VMA. Own gather, own non-blocking notifier |
| `unmap_vmas()` | munmap, exit; takes a `struct unmap_desc` (`mm/vma.h`) | gather started, mmap lock in either mode; it does not call `update_hiwater_rss()` (`unmap_region()` does before it, `exit_mmap()` does not) |
| `__zap_vma_range()` | static; reached by all of the above | gather, notifier started, and for hugetlb `hugetlb_zap_begin()` |

- `zap_vma_for_reaping()`: returns `-EBUSY` when the notifier would block;
  `__oom_reap_task_mm()` picks the VMAs and calls it.
- `.reaping`: makes `__zap_vma_range()` skip `uprobe_munmap()`.
- `lru_add_drain()`: not called by any of these.
- `unmap_vmas()` in `exit_mmap()`: runs under `mmap_read_lock()`; the write
  lock is taken only afterwards, for `free_pgtables()`.
- `zap_vma_range_batched()` on a hugetlb VMA: takes the hugetlb VMA lock and
  `i_mmap_rwsem` for write through `hugetlb_zap_begin()`, so the caller must
  hold neither.
- `struct zap_details`: has `skip_cows`, not an `even_cows` member;
  `unmap_mapping_pages()` sets `skip_cows = !even_cows`. `unmap_vmas()` sets
  only `zap_flags`.
