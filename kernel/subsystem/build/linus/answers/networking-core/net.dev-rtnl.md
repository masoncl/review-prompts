- `ASSERT_RTNL()`: tests `mutex_is_locked()`, so it passes when any task
  holds RTNL.
- `lockdep_rtnl_is_held()`: constant `true` without `CONFIG_PROVE_LOCKING`,
  so `rtnl_dereference()` and `rcu_dereference_rtnl()` check nothing then.
- RCU-or-per-netns-RTNL dereference: `rcu_dereference_rtnl_net()`. There is
  no rtnl_net_rcu_dereference and no rcu_dereference_bh_rtnl.
- `ASSERT_RTNL_NET()` and `lockdep_rtnl_net_is_held()` with
  `CONFIG_DEBUG_NET_SMALL_RTNL`: require both the global RTNL and
  `net->rtnl_mutex`.
- `CONFIG_DEBUG_NET_SMALL_RTNL`: selects `PROVE_LOCKING`.
- `RTNL_FLAG_DOIT_PERNET` and `RTNL_FLAG_DOIT_PERNET_WIP`: aliases of
  `RTNL_FLAG_DOIT_UNLOCKED` in `include/net/rtnetlink.h`;
  `rtnetlink_rcv_msg()` calls such a handler with no lock held.
- A handler with one of those flags locks for itself, for example with
  `rtnl_net_lock()` or `rtnl_nets_lock()`, which take the global RTNL first;
  no path takes only the per-netns mutex.
- `__rtnl_net_lock()` with `CONFIG_DEBUG_NET_SMALL_RTNL`: for a caller that
  already holds RTNL; it asserts `ASSERT_RTNL()`. Without the option it is an
  empty inline.
- Several namespaces, with `CONFIG_DEBUG_NET_SMALL_RTNL`: `init_net` first,
  then ascending `struct net` address; see `rtnl_net_cmp_locks()`.
- `rtnl_nets_lock()`: static in `net/core/rtnetlink.c`, not available to
  other files.
- `__rtnl_net_unlock()` with `CONFIG_DEBUG_NET_SMALL_RTNL`: calls
  `unregister_netdevice_many_net()` first, so unlocking unregisters devices
  that `unregister_netdevice_queue_net()` queued on `net->dev_unreg_head`.
- `unregister_netdevice_queue_net()` without the option: plain
  `unregister_netdevice_queue()`.
