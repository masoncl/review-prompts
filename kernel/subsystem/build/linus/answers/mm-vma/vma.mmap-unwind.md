- `__mmap_setup()` failure: the only jump straight to `abort_munmap`.
- `call_mmap_prepare()` failure: goes to `unacct_error`, like a
  `__mmap_new_vma()` failure, so the charge from `__mmap_setup()` is
  released.
- `abort_munmap`: before `vms_abort_munmap_vmas()` it does `fput(map.file)`
  when `map.file_doesnt_need_get` is set.
- Where a step's undo lives: state that outlives the helper is recorded in
  `struct mmap_state` and released at a label (`charged`,
  `file_doesnt_need_get`); anything else is released by the helper before it
  returns, as the `free_iter_vma` and `free_vma` labels of `__mmap_new_vma()`
  do.
- Last jump to the labels: the `__mmap_new_vma()` failure; nothing after the
  VMA is inserted reaches them.
- A `mmap` hook that fails: must release what it took itself; core calls no
  callback, it drops the file reference, clears the page tables
  (`unmap_region()` in `__mmap_new_file_vma()`) and frees the VMA.
