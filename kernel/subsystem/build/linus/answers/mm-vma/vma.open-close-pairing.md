- `mmap_prepare` files: the hook has no VMA; per-VMA setup belongs in
  `mapped`, which the core calls once for a newly allocated VMA.
- `mapped` in `vm_ops` that a legacy `mmap` hook assigns to `vma->vm_ops`
  itself: never called, and no error is raised; `call_vma_mapped()` is reached
  only from `mmap_action_complete()`, which a legacy hook reaches only through
  `compat_vma_mmap()` or `__compat_vma_mmap()`, as `uio_mmap()` does.
- Legacy `mmap` hook returns 0, when the file passed to `__mmap_region()` has
  no `mmap_prepare`: nothing later in `__mmap_region()` can fail, so the first
  `close` for that VMA comes from an unmap, not from an mmap error path.
- Legacy `mmap` hook returns an error: `mmap_file()` in `mm/internal.h`
  installs `vma_dummy_vm_ops`, so `close` is not called.
- **Unsafe usage**: taking a reference or allocating per-mapping state that
  `close` is to release, in the `mmap_prepare` hook.
  - Unsafe: after the hook returns 0, `__mmap_region()` may merge the range
    into a neighbour or fail in `__mmap_new_vma()`; neither path calls `close`
    or any other callback.
  - Safe: take it in `mapped`, as `tcmu_vma_mapped()` and `afs_mapped()` do.
- **Potentially unsafe usage**: a `close` that assumes `mapped` succeeded.
  - Unsafe: when `mapped` can return an error or `mmap_prepare` sets an mmap
    action; on either failure under `__mmap_region()`, `mmap_action_finish()`
    calls `do_munmap()` and `remove_vma()` reaches `close` with the `vm_ops`
    still installed.
  - Safe: when `mapped` always returns 0 and no action is set, as
    `afs_mapped()` with `afs_file_mmap_prepare()`.
- **Potentially unsafe usage**: `mapped` storing a per-VMA object through its
  `vm_private_data` argument.
  - Unsafe: when the mapping can merge at mmap time;
    `set_vma_user_defined_fields()` then overwrites `vm_ops` and
    `vm_private_data` of the VMA merged into, and `mapped` is not called.
  - Safe: when `mmap_prepare` sets a flag in `VMA_SPECIAL_FLAGS`, which
    `vma_merge_new_range()` refuses to merge; `remap_pfn_range_prepare()` sets
    `VMA_REMAP_FLAGS` for the remap actions.
