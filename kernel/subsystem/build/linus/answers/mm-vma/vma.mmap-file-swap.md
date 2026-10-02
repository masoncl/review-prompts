- Old file in `mmap_prepare` called from `call_mmap_prepare()`: mm core holds
  no VMA reference on it when the hook runs, so nothing is dropped; the
  caller's reference stays.
- Handover in `call_mmap_prepare()`: `file_doesnt_need_get` is set only after
  both the hook and `mmap_action_prepare()` returned 0; if either fails, core
  drops no reference on the new file.
- `compat_set_vma_from_desc()` in `mm/vma.h`: installs a changed
  `desc->vm_file` with `vma_set_file()`, which takes its own reference; the
  hook's reference is not consumed on this path.
- After a successful `mmap` hook: `map->file = vma->vm_file`, so the rest of
  `__mmap_region()` uses the new file.
- `vma_set_file()` in `mm/util.c`: calls `fput()` on the old `vma->vm_file`
  without a NULL test, so the VMA must already have a file.
- **Unsafe usage**: `mmap_prepare` stores in `desc->vm_file` a file that an
  adjacent VMA may already map.
  - Unsafe: `is_mergeable_vma()` then allows the merge, and no code on the
    merge path drops the handed-over reference.
  - Safe: a newly created file, as `shmem_zero_setup_desc()` in `mm/shmem.c`
    stores; no existing VMA has it as `vm_file`.
- **Unsafe usage**: `mmap_prepare` stores in `desc->vm_file` a file whose
  `f_op->mmap` is set and can fail.
  - Unsafe: on that failure `__mmap_new_file_vma()` does
    `fput(vma->vm_file)` and `abort_munmap` does `fput(map.file)` on the same
    file.
  - Safe: a shmem file, as `shmem_zero_setup_desc()` stores;
    `shmem_file_operations` sets only `mmap_prepare`, so
    `__mmap_new_file_vma()` returns before any hook.
- **Potentially unsafe usage**: assigning `vma->vm_file` directly in an
  `mmap` hook.
  - Unsafe: when the hook returns with `vma->vm_file` not holding exactly one
    reference for the VMA, or with the core's reference on the old file
    neither dropped nor kept for a later `fput()`; `__mmap_new_file_vma()`
    puts the installed file on failure and `remove_vma()` puts it on unmap.
  - Safe: `vma_set_file()`, as `dma_buf_mmap()` does.
  - Safe: `fput()` the old file and install a new file's creation reference,
    as `shmem_zero_setup()` does.
  - Safe: `get_file()` the new file and keep the old file's reference until
    `close`, dropping it at once if the hook fails, as `coda_file_mmap()`
    does with `coda_vm_close()`.
