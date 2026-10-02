- `struct vm_area_desc`: declared on the stack of `__mmap_region()` with
  `vm_ops = &vma_dummy_vm_ops` and `action.type = MMAP_NOTHING`;
  `set_desc_from_map()` fills the range, `pgoff`, `vm_file`, `vma_flags` and
  `page_prot` as the last step of `__mmap_setup()`.
- Successful `vma_merge_new_range()`: skips only `__mmap_new_vma()` (so no
  `mmap` hook) and `mmap_action_complete()`.
- After the merge or `__mmap_new_vma()`, in order:
  `set_vma_user_defined_fields()` (file with `mmap_prepare` only), then
  `__mmap_complete()`, then `mmap_action_complete()` (file with
  `mmap_prepare` and a newly allocated VMA only).
- `have_mmap_prepare`: computed once from the file passed to
  `__mmap_region()`, before any hook can replace the file.
- `mmap` hook test in `__mmap_new_file_vma()`: `!map->file->f_op->mmap`, on
  the file as it stands after `mmap_prepare`; the call goes `mmap_file()` →
  `vfs_mmap()`.
- `vfs_mmap()` in `include/linux/fs.h`: calls `compat_vma_mmap()` instead of
  `f_op->mmap` when the file it is given has `mmap_prepare`; a stacked `mmap`
  hook reaches this, for example `backing_file_mmap()`.
- `compat_vma_mmap()` in `mm/util.c`: runs `mmap_prepare` while the VMA
  already exists, on a desc built by `compat_set_desc_from_vma()`, then
  applies it with `compat_set_vma_from_desc()` and completes the action at
  once with `is_compat` true.
