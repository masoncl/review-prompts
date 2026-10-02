- Self-free example: `async_run_entry_fn()` in `kernel/async.c` calls
  `kfree(entry)` on its own container; the item is touched only by
  `INIT_WORK()`, one `queue_work_node()` and the function itself.
- `fs/aio.c`: `struct kioctx` has no `free_work` field; it has `free_rwork`, a
  `struct rcu_work` queued by `free_ioctx_reqs()`; `free_ioctx()` frees the ctx.
- Release-path example: `hci_adv_instances_clear()` in
  `net/bluetooth/hci_core.c` calls `disable_delayed_work_sync()` and then
  `kfree()` on each `struct adv_info`.
- Recycled address, same function, same pool: `assign_work()` puts the new item
  on the `scheduled` list of the worker still running the old one; if that
  running function waits for the new item, it deadlocks (comment on
  `find_worker_executing_work()`).
- **Potentially unsafe usage**: `flush_work()` followed by the free.
  - Unsafe: while any source can still queue the item; `__flush_work()` waits
    for the last queueing only and leaves the item enabled.
  - Safe: when the freeing code is the only queuer and queued once, as
    `schedule_on_each_cpu()` does before `free_percpu()`.
