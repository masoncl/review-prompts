- `vma_start_read()`: `static inline` in `mm/mmap_lock.c`, called only by
  `lock_vma_under_rcu()` and `lock_next_vma()`. Other files read-lock through
  those two, or under the mmap read lock with `vma_start_read_locked()` or
  `vma_start_read_locked_nested()`.
- Without `CONFIG_PER_VMA_LOCK`: `vma_start_read_locked()`,
  `vma_start_read_locked_nested()` and `lock_next_vma()` have no stub, so
  callers sit under `#ifdef`, for example `stack_map_lock_vma()` in
  `kernel/bpf/stackmap.c`.
- Keeping new readers out has two stages. While the writer waits,
  `__vma_start_exclude_readers()` holds `VM_REFCNT_EXCLUDE_READERS_FLAG` in
  `vm_refcnt`. After the wait `__vma_start_write()` writes `vm_lock_seq`, then
  `__vma_end_exclude_readers()` removes the flag, and from then on it is
  `vm_lock_seq` that makes `vma_start_read()` fail.
- Names: there is no __vma_enter_locked() or __vma_exit_locked() here;
  `__vma_start_exclude_readers()` and `__vma_end_exclude_readers()`, static in
  `mm/mmap_lock.c`, do that job.
- Names: the reader limit is `VM_REFCNT_LIMIT`; there is no VMA_REF_LIMIT.
  `VMA_LOCK_OFFSET` exists only in `tools/testing/vma/include/dup.h`; kernel
  code uses `VM_REFCNT_EXCLUDE_READERS_FLAG`.
- `vma_start_write_killable()` on a detached VMA (`vm_refcnt` 0): returns 0
  without waiting and still writes `vm_lock_seq`.
- `vma_start_write_killable()` returning `-EINTR`: the mmap write lock is still
  held, and VMAs write-locked earlier stay write-locked until
  `mmap_write_unlock()`.
- `dup_mmap()` in `mm/mmap.c` is the only caller of
  `vma_start_write_killable()` outside `tools/`: it jumps to `loop_out`, tears
  down the partly built child mm, and unlocks both mms at `out`.
