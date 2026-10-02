- Main count: `net->ns.__ns_ref`, a `refcount_t` in the embedded
  `struct ns_common`, defined in `include/linux/ns/ns_common_types.h`. Neither
  `struct ns_common` nor `struct net` has a member named `count`.
- `get_net()`, `maybe_get_net()`, `put_net()` and `check_net()`: under
  `CONFIG_NET_NS`, wrappers around `ns_ref_inc()`, `ns_ref_get()`,
  `ns_ref_put()` and `ns_ref_read()` in `include/linux/ns_common.h`.
- `init_net`: `ns_ref_inc()`, `ns_ref_get()` and `ns_ref_put()` return early
  when `is_ns_init_id()` is true, so its count is never changed and
  `maybe_get_net(&init_net)` always succeeds.
- `__ns_ref_active`: a separate counter, in `struct ns_tree`
  (`include/linux/ns/nstree_types.h`), which `struct ns_common` embeds.
  `get_net()` and `put_net()` do not change it, and it is not the passive
  count.
- Last `net_passive_dec()`, under `CONFIG_NET_NS`: frees `net->gen` at once
  but only queues the `struct net` on `defer_free_list`.
  `net_complete_free()` frees it on the next `cleanup_net()` run to reach it,
  after that run's `rcu_barrier()`.
- `get_net_ns_by_pid()`: calls `get_net()`, not `maybe_get_net()`. It reads
  `tsk->nsproxy->net_ns` under `task_lock()`, where the nsproxy holds a
  reference.
- `maybe_get_net()` under `rcu_read_lock()`: see `get_net_ns_by_id()` and
  `psp_nl_multicast_per_ns()`. No `for_each_net_rcu()` walker in this tree
  takes a reference.
- Keeping only the memory past the read section: call `net_passive_inc()`
  inside it, as `rtnl_net_dev_lock()` in `net/core/dev.c` does on the result of
  `dev_net_rcu()`. It then only locks and compares the pointer.
