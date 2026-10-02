- `vma_mark_detached()`: inline in `include/linux/mmap_lock.h`. It drops the
  attach reference with `__vma_refcount_put_return()` and returns if the count
  is 0. Otherwise it calls `__vma_exclude_readers_for_detach()` in
  `mm/mmap_lock.c`.
- Slow path of `vma_mark_detached()`: `__vma_exclude_readers_for_detach()`
  uses `__vma_start_exclude_readers()` and `__vma_end_exclude_readers()`.
- Dropping the attach reference does not by itself stop new readers: while
  `vm_refcnt` is non-zero and `VM_REFCNT_EXCLUDE_READERS_FLAG` is not yet set,
  `vma_start_read()` can still increment. Those readers fail the `vm_lock_seq`
  check and drop the reference; the wait covers them too.
- `tear_down_vmas()` in `mm/mmap.c`: calls `vma_mark_detached()` with no
  `vma_start_write()` of its own. In `exit_mmap()` the write locks come from
  `free_pgtables()` in `mm/memory.c`, which calls `vma_start_write()` only when
  `mm_wr_locked` in `struct unmap_desc` is set.
- `vms_gather_munmap_vmas()` in `mm/vma.c`: calls `vma_start_write()` and then
  `vma_mark_detached()` on each VMA.
