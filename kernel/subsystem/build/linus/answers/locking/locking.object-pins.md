- **Potentially unsafe usage**: an unconditional get (`refcount_inc()`,
  `kref_get()`) on an object found under `rcu_read_lock()`.
  - Unsafe: when the last reference can be dropped before the grace period,
    with only the free deferred. The reader can then find a zero count;
    `refcount_inc()` warns and saturates.
  - Safe: when a reference is itself dropped only from an RCU callback after
    the object is unpublished. `get_pid_task()` and
    `find_get_task_by_vpid()` in `kernel/pid.c` call `get_task_struct()`;
    `put_task_struct_rcu_user()` in `kernel/exit.c` defers `put_task_struct()`
    to `delayed_put_task_struct()` through `call_rcu()`, and `release_task()`
    calls it after `__exit_signal()` has unhashed the task.
- Conditional get, then identity re-check: `__inet_lookup_established()` in
  `net/ipv4/inet_hashtables.c`, `__fget_files_rcu()` in `fs/file.c`
  (`file_ref_get()`), `filemap_get_entry()` in `mm/filemap.c`.
- `igrab()` in `fs/inode.c`: tries `atomic_add_unless(&inode->i_count, 1, 0)`
  first; only on failure does it take `inode->i_lock` and test `I_FREEING`
  and `I_WILL_FREE`.
- `kfree_rcu()` release that a reader inside its section survives:
  `netif_set_alias()` in `net/core/dev.c`, read by `dev_get_alias()`.
  `dev_set_alias()` is a wrapper in `net/core/dev_api.c`.
- `kfree_rcu()` member type: `struct rcu_head` or `struct kvfree_rcu_head`
  (`include/linux/types.h`); `kvfree_rcu_arg_2()` in
  `include/linux/rcupdate.h` casts either.
