- `is_mergeable_vma()` in `mm/vma.c`: does not read `vm_ops`; its first test
  is `mpol_equal()` on `vmg->policy`.
- `vm_ops->close`: tested by `can_merge_remove_vma()`, called from
  `vma_merge_new_range()` and `vma_merge_existing_range()`, and only for a
  VMA the merge would delete.
- Proposed flags: held in `vmg->vma_flags` (`vma_flags_t`), in a union with
  `vmg->vm_flags`; `struct vma_merge_struct` has no member named flags.
- Special mappings: both merge functions return early when
  `vmg->vma_flags` has any bit of `VMA_SPECIAL_FLAGS`.
- Anonymous page offset: a VMA carries a second offset, read with
  `vma_start_anon_pgoff()`, and the vmg carries `anon_pgoff`.
- `needs_adjacent_anon_pgoff()`: true when `vmg->file` is set and
  `vma_flags_is_cow_mapping()` holds for `vmg->vma_flags`.
- When it is true, `can_vma_merge_before()` and `can_vma_merge_after()`
  also require the anonymous offsets to be contiguous, after the
  `vm_pgoff` test.
- Three-way merge: there is no are_anon_vmas_compatible(); the test of
  `prev->anon_vma` against `next->anon_vma` is inline at the end of
  `can_vma_merge_right()`.
- New attribute, member: add it to `struct vma_merge_struct` in
  `mm/vma.h`.
- New attribute, initialisers: `VMG_VMA_STATE()` copies each attribute
  from the VMA and needs a line for the new one.
- `VMG_STATE()` and `VMG_MMAP_STATE()` (the latter in `mm/vma.c`): leave
  `policy`, `uffd_ctx`, `anon_name` and `anon_vma` zero, so a new range
  proposes the zero value.
- New attribute, compare: one test in `is_mergeable_vma()` covers both
  sides and both merge functions.
- New attribute as a flag bit: compared automatically unless added to
  `VMA_IGNORE_MERGE_FLAGS`.
