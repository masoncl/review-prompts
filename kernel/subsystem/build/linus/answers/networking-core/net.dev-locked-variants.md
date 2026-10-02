- There is no netdev_ops_assert_locked here. The assert helpers in
  `include/net/netdev_lock.h` are:

| Helper | Ops-locked device | Other device |
|---|---|---|
| `netdev_assert_locked()` | lockdep: instance lock | lockdep: instance lock |
| `netdev_assert_locked_ops()` | lockdep: instance lock | no check |
| `netdev_assert_locked_ops_compat()` | lockdep: instance lock | `ASSERT_RTNL()` |

- `netdev_assert_locked_or_invisible()` and
  `netdev_assert_locked_ops_compat_or_invisible()`: same checks, made only in
  `NETREG_REGISTERED` or `NETREG_UNREGISTERING`. There is no
  netdev_ops_assert_locked_or_invisible.
- `netif_` prefix alone does not mean "lock held": `netif_napi_add()`,
  `netif_napi_del()`, `netif_napi_set_irq()` take `netdev_lock()` themselves.
- `_locked` suffix marks the lock-held form for NAPI: `netif_napi_add_locked()`,
  `netif_napi_del_locked()`, `napi_enable_locked()`, `napi_disable_locked()`.
- `netdev_` prefix is mixed: `netdev_state_change()` takes `netdev_lock_ops()`
  and calls `netif_state_change()`; `netdev_update_features()` expects the
  lock held on an ops-locked device.
- `dev_change_flags()`, `dev_set_promiscuity()`, `dev_set_allmulti()`: also
  call `netif_rx_mode_sync()` before unlocking; `netif_change_flags()`,
  `netif_set_promiscuity()` and `netif_set_allmulti()` do not, so an rx-mode
  update that `__dev_set_rx_mode()` queued stays queued.
- `netdev_lock_ops_to_full()` / `netdev_unlock_full_to_ops()`: for a caller
  already inside `netdev_lock_ops()`; lock a non-ops-locked device, only
  assert on an ops-locked one.
- **Unsafe usage**: calling a `dev_` wrapper from `net/core/dev_api.c` on an
  ops-locked device whose instance lock the caller holds; `netdev_lock_ops()`
  takes the same mutex again. `dev_set_threaded()` does so on any device.
  - Safe: call the `netif_` form, as `ipv6_add_dev()` in
    `net/ipv6/addrconf.c` does with `netif_disable_lro()` after
    `netdev_assert_locked_ops_compat()`.
  - Safe: call the `dev_` form from a `NETDEV_UNREGISTER` handler, which
    runs without the lock; `netdev_lock_ops()` then takes it, as
    `__bond_release_one()` does with `dev_close()` when
    `bond_slave_netdev_event()` handles `NETDEV_UNREGISTER`.
