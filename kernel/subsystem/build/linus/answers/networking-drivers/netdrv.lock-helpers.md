- There is no netdev_ops_assert_locked() or
  netdev_ops_assert_locked_or_invisible() here;
  `netdev_assert_locked_ops_compat()` and
  `netdev_assert_locked_ops_compat_or_invisible()` do that job.

| Assertion | Ops-locked device | Other device |
|---|---|---|
| `netdev_assert_locked()` | instance lock | instance lock |
| `netdev_assert_locked_or_invisible()` | instance lock, while `NETREG_REGISTERED` or `NETREG_UNREGISTERING` | same |
| `netdev_assert_locked_ops()` | instance lock | nothing |
| `netdev_assert_locked_ops_compat()` | instance lock | `ASSERT_RTNL()` |
| `netdev_assert_locked_ops_compat_or_invisible()` | instance lock, while `NETREG_REGISTERED` or `NETREG_UNREGISTERING` | `ASSERT_RTNL()`, in the same two states |

- `netdev_assert_locked_or_invisible()`: never falls back to `rtnl_lock`.
- `netdev_is_locked_ops_compat()` and `netdev_ops_lock_dereference()`: the
  lockdep predicate and RCU dereference for "ops protected" pointers.
- `netdev_get_by_index_lock_ops_compat()` and
  `for_each_netdev_lock_ops_compat_scoped()` in `net/core/dev.h`: look up and
  take the compat lock (instance lock or `rtnl_lock`) in one step.
- `dev_set_threaded()`: takes `netdev_lock()` unconditionally, unlike wrappers
  such as `dev_open()` in `net/core/dev_api.c`, which take
  `netdev_lock_ops()`.
- `netif_open()` and `netif_close()`: need `rtnl_lock` as well as the ops lock;
  `__dev_open()` and `__dev_close_many()` contain `ASSERT_RTNL()`.
- `netif_set_real_num_tx_queues()` and `netif_set_real_num_rx_queues()`: the
  only assertion in either is `netdev_assert_locked_ops_compat()`; neither
  contains `ASSERT_RTNL()`.
- `netif_set_real_num_tx_queues()` on a registered device also needs
  `rtnl_lock`: it calls `dev_qdisc_change_real_num_tx()`, which uses
  `rtnl_dereference()`.
- The assertion in `netif_set_real_num_tx_queues()` and
  `netif_set_real_num_rx_queues()` depends on `reg_state`, not on the device
  being up: tx asserts for `NETREG_REGISTERED` and `NETREG_UNREGISTERING`, rx
  for `NETREG_REGISTERED` only.
