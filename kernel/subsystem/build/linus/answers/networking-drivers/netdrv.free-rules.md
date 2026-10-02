- `priv_destructor`: the core calls it from two places only,
  `netdev_run_todo()` (rtnl not held, references gone, before the optional
  `free_netdev()`) and the error path of `register_netdevice()` (rtnl held).
  `free_netdev()` never calls it.
- Failed `register_netdevice()`, by where it failed:

| Failure point | `ndo_uninit` | `priv_destructor` |
|---|---|---|
| `ethtool_check_ops()`, name, `ndo_init` | not called | not called |
| after `ndo_init`, up to `netdev_register_kobject()` | called before return | called before return |
| `NETDEV_REGISTER` notifier | called before return, from `unregister_netdevice_many_notify()` | called later, from `netdev_run_todo()` |

- `needs_free_netdev` after a failed registration: the caller frees in every
  case; only the notifier-failure path clears the flag.
- `needs_free_netdev` after `unregister_netdev()`: `netdev_run_todo()` runs
  inside `rtnl_unlock()`, so the device is already freed when
  `unregister_netdev()` returns.
- `free_netdev()` under rtnl right after `unregister_netdevice()`, as in
  `qmimux_register_device()`: `reg_state` is `NETREG_UNREGISTERING`, so it
  only sets `needs_free_netdev`; `netdev_run_todo()` frees the device at
  `rtnl_unlock()`. The same holds for the caller's `free_netdev()` after a
  `register_netdevice()` that failed in the `NETDEV_REGISTER` notifier:
  that path has called `unregister_netdevice_queue()`, so the device is
  `NETREG_UNREGISTERING` and `priv_destructor` has not run yet.
- `rtnl_newlink_create()`: calls `free_netdev()` itself when `newlink` or
  `register_netdevice()` fails; a `newlink` implementation must not free the
  device it was passed.
- `devm_alloc_etherdev_mqs()`: `devm_free_netdev()` frees at devres release;
  the driver does not call `free_netdev()`.
- **Unsafe usage**: reading anything through `netdev_priv()` after
  `free_netdev()`, or after `unregister_netdev()` when `needs_free_netdev` is
  set.
  - Safe: release what hangs off priv first and call `free_netdev()` last, as
    `igb_remove()` does; `netdev_release()` frees priv with the device.
- **Unsafe usage**: freeing memory that holds a `struct napi_struct` still on
  `dev->napi_list` before `free_netdev()`; `netdev_napi_exit()` dereferences
  each one.
  - Safe: `netif_napi_del()` before freeing that memory, or
    `__netif_napi_del()` and an RCU grace period, as `ixgbe_free_q_vector()`
    does with `kfree_rcu()`.
  - Safe: the NAPI struct lives inside the `netdev_priv()` area, as `napi` in
    `struct rtl8169_private`; `free_netdev()` runs `netdev_napi_exit()`
    before the device memory is freed.
