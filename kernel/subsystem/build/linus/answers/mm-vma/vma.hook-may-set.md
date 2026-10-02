- `desc->file`: input only; the replaceable file is `desc->vm_file`.
- `enum mmap_action_type` in `include/linux/mm_types.h`: five values;
  besides nothing, PFN remap and I/O remap there are `MMAP_SIMPLE_IO_REMAP`
  (`mmap_action_simple_ioremap()`) and `MMAP_MAP_KERNEL_PAGES`
  (`mmap_action_map_kernel_pages()`).
- `mmap_action_prepare()`: runs inside `call_mmap_prepare()` before the
  copy-back and edits the desc itself: `remap_pfn_range_prepare()` sets
  `VMA_REMAP_FLAGS` and may write `desc->pgoff`;
  `map_kernel_pages_prepare()` sets `VMA_MIXEDMAP_BIT`.
- I/O remap types: `mmap_action_prepare()` rewrites `MMAP_IO_REMAP_PFN` and
  `MMAP_SIMPLE_IO_REMAP` to `MMAP_REMAP_PFN`; `mmap_action_complete()` warns
  and fails with `-EINVAL` if it still sees either.
- `struct mmap_action`: has no success hook and no error hook.
- `error_override` in `struct mmap_action`: replaces the error returned from
  a failed action or a failed `mapped` when not called from the compat path;
  `check_mmap_action()` rejects a value that is not an error code.
- `mapped` in `struct vm_operations_struct`: the per-VMA callback;
  `call_vma_mapped()` in `mm/util.c` calls it from `mmap_action_finish()`
  after the action succeeds, also for `MMAP_NOTHING`.
- `hide_from_rmap_until_complete`: `__mmap_new_vma()` passes it to
  `vma_link_file()` as `hold_rmap_lock`, and `vma_link_file()` then returns
  with the file's `i_mmap_rwsem` still held for write;
  `maybe_rmap_unlock_action()` in `mm/internal.h`, called from
  `mmap_action_finish()`, releases it; `compat_vma_mmap()` forces it to
  false.
