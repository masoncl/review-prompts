- Modify functions in this tree: `vma_modify_flags()`,
  `vma_modify_name()`, `vma_modify_policy()`, `vma_modify_flags_uffd()`;
  there is no vma_modify_flags_name().
- `give_up_on_oom` (set by `vma_modify_flags_uffd()` on request): a merge
  OOM is not reported; `vma_modify()` returns the unmerged VMA.
- Split failure in `vma_modify()`: the error can come from
  `vm_ops->may_split`, not only `-ENOMEM`.
- Failed second split: the first split is not undone, so the passed-in
  VMA is valid but its `vm_start` has already moved.
- VMA write lock: the modify functions do not assert it, and when no
  neighbour can merge and no split is needed nothing write-locks the
  returned VMA.
- Callers lock the returned VMA before changing it: `mprotect_fixup()`,
  `madvise_update_vma()` and `__mseal_range()` call `vma_start_write()`.
- Returned VMA after a merge: can be larger than the requested range;
  `mprotect_fixup()` keeps using its own `start` and `end` for
  `change_protection()`.
- `vmg_nomem()` after `vma_merge_new_range()`: true only when
  `commit_merge()` failed and `give_up_on_oom` is clear.
- `vma_expand()`: returns on `dup_anon_vma()` failure before it sets
  `VMA_MERGE_ERROR_NOMEM`, so that OOM reads as a plain no-merge.
- `__mmap_region()` and `copy_vma()`: do not call `vmg_nomem()`; any NULL
  leads to allocating a new VMA.
- `do_brk_flags()`: the one caller of `vma_merge_new_range()` that fails
  on `vmg_nomem()`.
- `vma_merge_extend()`: NULL covers both no-merge and OOM;
  `expand_vma_in_place()` in `mm/mremap.c` returns `-ENOMEM` for either.
- `copy_vma()`: also returns NULL when the destination range is occupied.
- `copy_vma()` and `*vmap`: changes only when the merge deleted the
  source VMA; otherwise left as passed.
- **Unsafe usage**: dereferencing the source VMA pointer held before
  `copy_vma()` after it returns.
  - Unsafe: when the new range merged with `prev` and deleted the source,
    the old pointer is freed.
  - Safe: pass the address of a local and use the local afterwards, as
    `copy_vma_and_data()` in `mm/mremap.c` does; it also sets
    `vrm->vmi_needs_invalidate` when the pointer changed.
- **Potentially unsafe usage**: using the VMA passed to a modify function
  after a successful return.
  - Unsafe: when the old pointer is used with no test that the returned
    VMA is the same one; if the range covered the whole VMA and a merge
    happened, the passed VMA is freed.
  - Safe: replace the local with the return value, as `mbind_range()` in
    `mm/mempolicy.c` does before `vma_replace_policy()`.
  - Safe: after testing that the returned VMA is the one passed, as
    `setup_arg_pages()` in `fs/exec.c` does with `BUG_ON(prev != vma)`
    after `mprotect_fixup()`; `vma_modify()` returns either the merge
    target or the VMA passed.
  - Safe: after an `IS_ERR()` return the passed VMA is still valid;
    `apply_mlockall_flags()` in `mm/mlock.c` sets `prev` from it.
