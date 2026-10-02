- VMA linked list: none in this tree; `mm->mm_mt` is the only per-mm index of
  VMAs, and prev/next come from the `struct vma_iterator`.
- Build scope: `mm/vma.c` and `mm/vma_exec.c` are built only under
  `CONFIG_MMU`; `mm/vma_init.c` (allocation, duplication, freeing) is built
  for nommu too. See `mm/Makefile`.
- Two page offsets per `struct vm_area_struct`: `vm_pgoff`, and an anonymous
  page offset read with `vma_start_anon_pgoff()` (`include/linux/mm.h`) and
  written with `vma_set_anon_pgoff()` (`mm/vma.h`).
  - Pure anonymous VMA, under `CONFIG_MMU`: the two are equal; `do_mmap()` in
    `mm/nommu.c` sets only `vm_pgoff`.
- `vma_flags_t`: a bitmap type. `vma->flags` holds it, in a union with
  `const vm_flags_t vm_flags`, so both name the same storage.
  `struct vma_merge_struct` and `struct mmap_state` have a like union, but
  the bitmap member is named `vma_flags` and `vm_flags` is not const;
  `struct vm_area_desc` has only `vma_flags`.
- Attached and detached: the state of `vm_refcnt`, not tree membership.
  - `vms_gather_munmap_vmas()` marks VMAs detached while they are still in
    `mm->mm_mt`; they leave the tree later.
  - Without `CONFIG_PER_VMA_LOCK`: `vma_mark_attached()` and
    `vma_mark_detached()` are empty, `vma_is_attached()` returns true.
- `struct vma_munmap_struct` side tree: indexed by a counter, 0 to
  `vma_count` - 1, not by address.
- `struct vma_munmap_struct` on the `munmap()` path
  (`do_vmi_align_munmap()`): gather, clear the range in `mm->mm_mt`, then
  `vms_complete_munmap_vmas()` clears page tables and frees the VMAs.
- `struct vma_munmap_struct` on the `mmap()` path: `vms_clean_up_area()`,
  called from `__mmap_setup()`, clears page tables and calls `vma_close()`
  before any new VMA exists.
  - `vms_complete_munmap_vmas()`, called from `__mmap_complete()`, then only
    does the accounting and frees the old VMAs.
  - `vms->clear_ptes` records which side of that point the unmap is on;
    `vms_abort_munmap_vmas()` reattaches only while it is still true.
- `struct mmap_state`: embeds the `struct vma_munmap_struct` and its side
  tree (`vms`, `mas_detach`, `mt_detach`). It holds no
  `struct vma_merge_struct`; `VMG_MMAP_STATE()` builds one from it.
- `struct unmap_desc` (`mm/vma.h`): the range argument of `unmap_region()`,
  `unmap_vmas()` and `free_pgtables()`. It holds three separate limits: the
  VMA range to zap, the page table floor and ceiling to free, and the bound
  of the tree walk. Build it with `UNMAP_STATE()` or `unmap_all_init()`;
  `unmap_pgtable_init()` only re-aims an existing one, as `exit_mmap()` does
  before `free_pgtables()`.
- `struct vma_prepare`: not used by every bounds change.
  `expand_upwards()` and `expand_downwards()` take the anon_vma lock and
  call `anon_rmap_tree_pre_update_vma()` and
  `anon_rmap_tree_post_update_vma()` themselves.
- `struct unlink_vma_file_batch`: used by `free_pgtables()` in `mm/memory.c`
  to remove up to eight consecutive VMAs of one file from `i_mmap` under a
  single `i_mmap_lock_write()`.
