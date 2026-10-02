- Failed fork: `dup_mmap()` in `mm/mmap.c` tears the child down itself, under
  both write locks. It does not store `XA_ZERO_ENTRY`; nothing under `mm/`
  tests `xa_is_zero()`.
- Failure sequence: set `MMF_OOM_SKIP`; `unmap_region()`; `tear_down_vmas()`;
  `vm_unacct_memory()`; `__mt_destroy()`; set `MMF_UNSTABLE`; unlock.
- Child tree after failure: empty. `exit_mmap()`, reached from `mmput()`,
  finds no VMA and jumps to its `destroy` label.
- Teardown bound `end`, also written to `unmap.tree_end`:

| Failure | `end` |
|---|---|
| no VMA stored yet (`map_count` is 0) | 0; unmap and teardown skipped |
| before the copy of `mpnt` is stored | `mpnt->vm_start` |
| `copy_page_range()` on a stored VMA | start of the next VMA, or `ULONG_MAX` |
| `arch_dup_mmap()` | `ULONG_MAX` |

- Entries at or above `end`: still the parent's VMAs from `__mt_dup()`.
  `__mt_destroy()` frees only tree nodes, so teardown that passes `end` would
  free parent VMAs.
- `tear_down_vmas()`: calls `remove_vma()` on each stored VMA, so every
  `vm_ops->open()` is paired with a close; it does not decrement `map_count`.
- Left stale on the child mm: `map_count`, and `total_vm`, `data_vm`,
  `exec_vm`, `stack_vm` copied from the parent.
- `__mt_dup()` failure: jumps to `out`, past the failure block; neither
  `MMF_OOM_SKIP` nor `MMF_UNSTABLE` is set.
- `mmap_write_lock_killable(oldmm)` failure: returns `-EINTR` with the child
  untouched.
- `vma_start_write_killable()` is what locks each parent VMA; it can fail,
  making that VMA the failure point.
- `dup_mm()` in `kernel/fork.c`, not `copy_mm()`, calls `mmput()` on failure,
  then `uprobe_end_dup_mmap()`. `uprobe_start_dup_mmap()` is called there too;
  `dup_mmap()` itself calls `uprobe_dup_mmap()`.
- Flag tests in `dup_mmap()` use `vma_test()` with `VMA_DONTCOPY_BIT`,
  `VMA_WIPEONFORK_BIT`, `VMA_ACCOUNT_BIT`; a search for `VM_DONTCOPY` in
  `mm/mmap.c` finds nothing.
- mlock bits: cleared by `vma_clear_flags_mask(tmp, VMA_LOCKED_MASK)`, not
  `vm_flags_clear()`.
- There is no vma_lock_alloc() here; `vm_area_dup()` in `mm/vma_init.c` calls
  `vma_lock_init(new, true)`.
- `vm_area_dup()`: copies field by field in `vm_area_init_from()`, not the
  whole struct. A field missing from that function is left out of the child.
- `pfnmap_track_ctx`, under `__HAVE_PFNMAP_TRACKING`: shared with the parent
  by `kref_get()`, not reset; `vm_area_dup()` returns NULL if the count is
  saturated.
- `vma_needs_copy()` in `mm/memory.c`: true if the child VMA has any
  `VM_COPY_ON_FORK` bit, or the parent VMA has an `anon_vma`. It has no
  hugetlb test, so a hugetlb VMA with neither is not copied.
- `VM_COPY_ON_FORK` is tested on the child VMA, after `dup_userfaultfd()` may
  have cleared the uffd bits there.
