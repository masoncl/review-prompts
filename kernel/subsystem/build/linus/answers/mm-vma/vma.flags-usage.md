- **Potentially unsafe usage**: changing flags with a helper that neither
  locks nor asserts: `vma_set_flags()`, `vma_set_flags_mask()`,
  `vma_clear_flags()`, `vma_clear_flags_mask()`, `vma_flags_reset_once()`, or
  a direct `vma->flags = x`.
  - Unsafe: on a VMA that is in the tree and that the caller has not
    write-locked; `vm_flags_reset()` asserts the same requirement with
    `vma_assert_write_locked()`.
  - Safe: after `vma_start_write()` under the mmap write lock, as
    `mprotect_fixup()`, `madvise_update_vma()` and `__mseal_range()` do.
  - Safe: on a VMA not yet inserted, as `create_init_stack_vma()` in
    `mm/vma_exec.c` and `__install_special_mapping()` do.
  - Safe: inside an `->mmap` hook called from `__mmap_new_file_vma()`, where
    the VMA is still detached, as `hugetlbfs_file_mmap()` does;
    `__mmap_new_vma()` calls `vma_iter_store_new()` only after the hook.
- **Unsafe usage**: `vm_flags_reset()` in an `->mmap` hook with no earlier
  write lock.
  - Unsafe: `__mmap_new_vma()` calls `vma_start_write()` only after the hook
    returns, so `vma_assert_write_locked()` warns, with `CONFIG_PER_VMA_LOCK`
    and `CONFIG_DEBUG_VM`.
  - Safe: `vm_flags_mod()`, `vm_flags_set()` or `vm_flags_clear()`, which lock
    first, as `mmap_vmcore()` in `fs/proc/vmcore.c` does.
  - Safe: `vma_start_write()` and then `vm_flags_reset()`, as
    `userfaultfd_set_ctx()` in `mm/userfaultfd.c` does.
- `remap_pfn_range()`: sets `VMA_REMAP_FLAGS` through `vma_set_flags_mask()` in
  `remap_pfn_range_prepare_vma()`; it does not call `vm_flags_set()` and for
  that write neither takes nor asserts the VMA write lock.
- `vma_modify_flags()`: takes a `vma_flags_t *` and, on a successful merge,
  writes the merged VMA's flags back through it, so sticky flags can be added;
  store the value from the pointer afterwards, not the value passed in.
- After `vma_modify_flags()`: callers lock and store themselves;
  `mprotect_fixup()` and `mlock_vma_pages_range()` use
  `vma_flags_reset_once()`, `madvise_update_vma()` assigns `vma->flags`. None
  of them calls `vm_flags_reset()`.
- New VMA in `mm/`: `__mmap_new_vma()` assigns `vma->flags`; `vma_init()`
  leaves the flags zero from its `memset()`. `vm_flags_init()` is used when
  copying, by `vm_area_init_from()` in `mm/vma_init.c`.
- `->mmap` hook and merging: after the hook `__mmap_new_file_vma()` copies
  `vma->flags` into `map->vma_flags`; no merge is attempted afterwards.
- `->mmap_prepare` hook: change `desc->vma_flags` with `vma_desc_set_flags()`
  or `vma_desc_clear_flags()`, as `secretmem_mmap_prepare()` does;
  `call_mmap_prepare()` copies the result into the mapping state before the
  merge attempt.
- There is no hugetlbfs_file_mmap_prepare() here, and `shmem_mmap_prepare()`
  changes no flags.
- Atomic exception: `vma_set_atomic_flag()` with `VMA_MAYBE_GUARD_BIT` may run
  under the mmap read lock or a VMA read lock, as `madvise_guard_install()` in
  `mm/madvise.c` does.
