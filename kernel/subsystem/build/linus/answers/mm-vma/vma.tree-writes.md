- `vma_iter_store_new()`: for a detached VMA; it calls
  `vma_mark_attached()`, which asserts write-locked and detached, so
  `vma_start_write()` comes first.
- `vma_iter_store_overwrite()`: for a VMA already in the tree whose range
  changed; it calls `vma_assert_attached()`.
- There is no vma_iter_store() here.
- `vma_iter_store_gfp()`: only `do_brk_flags()` calls it; `vma_link()`
  preallocates and calls `vma_iter_store_new()`.
- There is no vma_iter_bulk_alloc() here; `dup_mmap()` copies the tree with
  `__mt_dup()` and replaces entries with `vma_iter_bulk_store()`.
- `vma_iter_clear_gfp()`, `vma_iter_bulk_store()` and `vma_iter_free()` are
  defined in `include/linux/mm.h`, the rest in `mm/vma.h`.
- Stored range: the store helpers take it from `vma->vm_start` and
  `vma->vm_end`, so both must be final before the store, as in
  `commit_merge()`.
- `vma_iter_clear()`: takes the range from `vma_iter_config()`;
  `vma_shrink()` clears before it writes `vm_end`.
- One preallocation serves one store: `mas_store_prealloc()` ends with
  `mas_destroy()`.
- `vma_iter_store_new()`, `vma_iter_store_overwrite()` and
  `vma_iter_clear()` return void; `mas_store_prealloc()` checks the result
  with `MAS_WR_BUG_ON()`.
- **Unsafe usage**: a tree write that can return an error after changes
  that cannot be undone.
  - Safe: `vma_iter_config()` and `vma_iter_prealloc()` for the stored
    range before `vma_prepare()`, then a preallocated store, as
    `commit_merge()` and `__split_vma()` do.
  - Safe: `vma_iter_clear_gfp()` before the point of no return, with
    `reattach_vmas()` on failure, as `do_vmi_align_munmap()` does.
  - Safe: `mas_store_gfp()` with `__GFP_NOFAIL`, as
    `vms_abort_munmap_vmas()` does once PTEs are already cleared.
