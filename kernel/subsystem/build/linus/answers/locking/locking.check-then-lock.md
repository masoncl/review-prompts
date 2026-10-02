- `list_empty_careful()` on the removed entry returning true: everything the
  remover wrote before `list_del_init_careful()` is visible to the caller.
  The `smp_load_acquire()` of `head->next` pairs with the
  `smp_store_release()` in `list_del_init_careful()`, both in
  `include/linux/list.h`.
- With plain `list_del_init()` on the other side there is no such ordering;
  only the two-pointer test remains.
- **Potentially unsafe usage**: acting under the lock on the result of an
  unlocked test, without testing again.
  - Unsafe: when the action is wrong if the state changed between the test
    and the lock.
  - Safe: when the locked action is harmless in either state. `finish_wait()`
    in `kernel/sched/wait.c` takes `wq_head->lock` and calls
    `list_del_init()`, which leaves an already removed entry self-linked.
- Check, lock, re-check: `pte_alloc()` in `include/linux/mm.h` tests
  `pmd_none()` unlocked; `pmd_install()` in `mm/memory.c` tests it again
  under `pmd_lock()`, and `__pte_alloc()` frees the unused table.
- `list_empty_careful()` skipping the lock: `finish_wait()` with
  `autoremove_wake_function()`, which removes the entry with
  `list_del_init_careful()`.
