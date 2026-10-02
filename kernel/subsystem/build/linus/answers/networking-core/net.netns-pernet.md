- RTNL callback: `exit_rtnl` in `struct pernet_operations`. There is no
  exit_batch_rtnl in this tree.
- `exit_rtnl` phase: runs after the grace period and before any `exit`. See
  `ops_exit_rtnl_list()` in `net/core/net_namespace.c`.
- `exit_rtnl` iteration: called once per net per op, with nets in the outer loop
  and ops in reverse inside. `pre_exit` and `exit` iterate the other way round.
- `exit_rtnl` phase is skipped when no op in the walked list sets `exit_rtnl`.
- Per-net RTNL in that phase: `__rtnl_net_lock()` is a real mutex only under
  `CONFIG_DEBUG_NET_SMALL_RTNL`, and an empty stub otherwise.
- `exit` and `exit_batch`: interleaved per op. `ops_exit_list()` runs one op's
  `exit` for every net, then that op's `exit_batch`, then moves to the next op.
- `exit_batch` with its own `rtnl_lock()`: still used, for example by
  `default_device_exit_batch()` in `net/core/dev.c`.
- Core grace period: `synchronize_rcu_expedited()` from `cleanup_net()`. It is
  `synchronize_rcu()` from `setup_net()` unwind and from `ops_undo_single()`.
- Waiting in a handler: no code forbids it in any callback. All run in process
  context, and RTNL is a mutex.
- Cost of a wait: once per net in `pre_exit`, `exit` and `exit_rtnl`, once per
  batch in `exit_batch`.
- Waits under RTNL exist in-tree: `ops_exit_rtnl_list()` ends with
  `unregister_netdevice_many()`, which calls `synchronize_net()` when the kill
  list is not empty. `nexthop_net_exit_rtnl()` also reaches
  `synchronize_net()`, when a removed nexthop is a member of a group.
- `exit_rtnl` is not limited to queueing devices: `fib_net_exit_rtnl()` and
  `nexthop_net_exit_rtnl()` flush tables.
- `synchronize_net()`: expedited when `from_cleanup_net()` or
  `rtnl_is_locked()` is true. A plain `synchronize_rcu()` in a handler is not.
- Final `rcu_barrier()` in `cleanup_net()`: does not cover the
  `net_generic()` areas. `ops_free_list()` has already freed each op's
  `net_generic()` area with `kfree()`.
- **Unsafe usage**: a `call_rcu()` callback queued from an exit handler that
  reads the op's `net_generic()` area; `ops_free_list()` frees the area with
  no wait for callbacks.
  - Safe: unpublish in `pre_exit` and free in `exit`, as
    `iptable_filter_net_pre_exit()` and `iptable_filter_net_exit()` in
    `net/ipv4/netfilter/iptable_filter.c` do. `ops_undo_list()` puts the grace
    period between them.
- Unregistering: `unregister_pernet_subsys()` and `unregister_pernet_device()`
  run the same sequence through `ops_undo_single()`. It covers every live net,
  `init_net` included, with `pernet_ops_rwsem` held for write.
