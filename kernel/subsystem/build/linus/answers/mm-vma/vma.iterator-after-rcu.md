- `vma_start_read()`: returns with RCU held only on success. Every failure
  return has already called `rcu_read_unlock()`: `NULL`, `ERR_PTR(-EAGAIN)` and
  the `vm_mm` mismatch path. The caller must not unlock again.
- `lock_next_vma()`: entered with RCU held and returns with RCU held on every
  path. Inside, it drops and retakes RCU on the `-EAGAIN` retry, when the lock
  attempt fails, and when either check after locking fails.
- `lock_next_vma()` can sleep: the fallback
  `lock_next_vma_under_mmap_lock()` calls `mmap_read_lock_killable()` after one
  `rcu_read_unlock()`. Other RCU-protected pointers the caller loaded before
  the call are not protected across it.
- `lock_next_vma()` return values: a read-locked VMA, `NULL` at the end,
  `ERR_PTR(-EINTR)`, or `ERR_PTR(-EAGAIN)` when `vma_start_read_locked()` fails
  under the mmap lock. The comment in `include/linux/mmap_lock.h` lists only
  `-EINTR`; `proc_get_vma()` in `fs/proc/task_mmu.c` handles both.
- Iterator on return from `lock_next_vma()`: on every path that dropped RCU it
  has already called `vma_iter_set()`, to `vma->vm_end` after a successful
  fallback and to `from_addr` otherwise. A caller that stayed in the RCU
  section may call `lock_next_vma()` again with no reset.
- **Potentially unsafe usage**: stepping a `struct vma_iterator` that was
  walked in an RCU section the caller has since left.
  - Unsafe: when the next `vma_next()` or `lock_next_vma()` runs with no
    `vma_iter_set()`, `vma_iter_init()` or `mas_set()` since the new
    `rcu_read_lock()`; maple nodes are freed through `ma_free_rcu()` in
    `lib/maple_tree.c`, so the cached node may be gone.
  - Safe: reset right after retaking RCU, as `reacquire_rcu()` in
    `fs/proc/task_mmu.c` does with `locked_vma->vm_end`.
  - Safe: reset after switching to the mmap lock, as `fallback_to_mmap_lock()`
    in `fs/proc/task_mmu.c` does.
  - Safe: an iterator that is not used again, as in
    `query_vma_find_by_addr()` in `fs/proc/task_mmu.c`.
