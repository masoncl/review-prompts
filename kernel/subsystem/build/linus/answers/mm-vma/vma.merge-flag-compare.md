- `is_mergeable_vma()`: builds the difference with `vma_flags_diff_pair()`
  on `vma->flags` and `vmg->vma_flags`, then removes
  `VMA_IGNORE_MERGE_FLAGS` with `vma_flags_clear_mask()`.
- Mask names: `VMA_IGNORE_MERGE_FLAGS` is defined as `VMA_STICKY_FLAGS` in
  `include/linux/mm.h`; VM_IGNORE_MERGE and VM_STICKY are not defined.
- `VMA_STICKY_FLAGS`: `VMA_SOFTDIRTY_BIT` and `VMA_MAYBE_GUARD_BIT` under
  `CONFIG_MEM_SOFT_DIRTY`, otherwise `VMA_MAYBE_GUARD_BIT` alone.
- Sticky bits on the merged VMA: `vma_merge_existing_range()` and
  `vma_expand()` collect them and set them on the target after
  `commit_merge()` succeeds.
- Sources collected: the proposed `vmg->vma_flags`, the target, and `prev`
  or `next` when that side takes part; `middle` contributes only through
  `vmg->vma_flags`.
- `vma_modify_flags_uffd()`: takes `const vma_flags_t *` and writes nothing
  back.
- New mappings: `VMA_SOFTDIRTY_BIT` is set on the VMA after the merge
  attempt, in `__mmap_complete()` and at the end of `do_brk_flags()`, both
  gated by `pgtable_supports_soft_dirty()`.
- **Unsafe usage**: overwriting the returned VMA's flags with a copy of
  the requested flags taken before `vma_modify_flags()`.
  - Unsafe: after a merge, a sticky bit contributed by a neighbour is
    cleared from the merged VMA.
  - Safe: overwrite with the value written back through the pointer, as
    `mprotect_fixup()` does with `vma_flags_reset_once()`.
  - Safe: only add bits to the returned VMA, as `__mseal_range()` does
    with `vma_set_flags()`.
  - Safe: derive the new value from the returned VMA's own flags, as
    `userfaultfd_set_ctx()` does.
