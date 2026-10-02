- `vma_prepare()`: takes no VMA lock; the caller calls `vma_start_write()`
  on every VMA that changes, is inserted or is removed before it.
- Preallocation and `vma_start_write()`: order is not fixed; `__split_vma()`
  and `vma_shrink()` preallocate first, merges write-lock first and
  preallocate in `commit_merge()`; both precede `vma_prepare()`.
- Fallible work after `vma_start_write()`: allowed up to `vma_prepare()`;
  `dup_anon_vma()` runs there in a merge.
- From `vma_prepare()` to `vma_complete()`: no call that can fail, in
  `__split_vma()`, `commit_merge()` and `vma_shrink()`.
- `vma_adjust_trans_huge()`: runs after `vma_prepare()` and before the range
  is written, in all three.
- `hugetlb_split()`: called at the same point by `__split_vma()` for a
  hugetlb VMA; it asserts the VMA write lock and `i_mmap_rwsem` held for
  write.
- `vma_complete()` stores `vp->insert` after the file-tree reinsertion and
  before `anon_rmap_tree_post_update_vma()`, with the rmap locks that
  `vma_prepare()` took still held.
- Removed VMA in `vma_complete()`: `unlink_anon_vmas()` drops its anon
  links; there is no anon_vma_merge() here.
- Tree helper names inside `vma_prepare()` and `vma_complete()`: as in
  "Reverse-map trees".
