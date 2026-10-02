- `netdev_wait_allrefs_any()`: waits for `netdev_refcnt_read()` to equal 1,
  not 0; the last count is the one set in `alloc_netdev_mqs()`.
- `netdev_run_todo()`: sets `NETREG_UNREGISTERED` under `netdev_lock()`
  before the wait, right after `rcu_barrier()`.
- Code that runs while references drain sees `NETREG_UNREGISTERED`, not
  `NETREG_UNREGISTERING`.
- Rebroadcast of `NETDEV_UNREGISTER`: every second, under RTNL and
  `__rtnl_net_lock()`, without the instance lock.
- "waiting for %s to become free": every `netdev_unregister_timeout_secs`
  (default 10), followed by `ref_tracker_dir_print()`.
- `free_netdev()`: never calls `priv_destructor`; in the core only
  `register_netdevice()` (error path) and `netdev_run_todo()` do.
- `free_netdev()` on a `NETREG_UNREGISTERING` device: sets
  `needs_free_netdev`, returns; `netdev_run_todo()` frees. It asserts RTNL.
- `needs_free_netdev` set: the device is freed inside the `rtnl_unlock()`
  that follows `unregister_netdevice()`; `netdev_priv()` is gone when
  `rtnl_unlock()` or `unregister_netdev()` returns.
- After a failed `register_netdevice()` the caller has to call
  `free_netdev()`; the driver's `needs_free_netdev` setting is never acted
  on. What the core already ran:

| Failure point | `ndo_uninit` | `priv_destructor` | `reg_state` on return |
|---|---|---|---|
| before `ndo_init`, or `ndo_init` itself | no | no | `NETREG_UNINITIALIZED` |
| after `ndo_init`, through `NETDEV_POST_INIT` | yes | yes | `NETREG_UNINITIALIZED` |
| `netdev_register_kobject()` | yes | yes | `NETREG_UNREGISTERED` |
| `NETDEV_REGISTER` notifier | yes, by full unregister | yes, in `netdev_run_todo()` | `NETREG_UNREGISTERING` until RTNL is dropped |

- `NETDEV_REGISTER` notifier failure: `register_netdevice()` clears
  `needs_free_netdev` and calls `unregister_netdevice_queue()`; a
  `free_netdev()` under the same RTNL hold is deferred as above, as in
  `rtnl_newlink_create()`.
- **Potentially unsafe usage**: freeing in the caller's error path what
  `priv_destructor` frees, after `register_netdevice()` failed later than
  `ndo_init`.
  - Unsafe: when `priv_destructor` was already set when
    `register_netdevice()` ran and the caller frees without testing whether
    it already ran; `register_netdevice()` calls it at `err_uninit`, so the
    state is freed twice.
  - Safe: when the destructor clears `dev->priv_destructor` and the caller
    tests that pointer first, as `ipoib_intf_free()` and
    `__ipoib_vlan_add()` do; `register_netdevice()` and `netdev_run_todo()`
    test the same pointer.
  - Safe: set `priv_destructor` only after registration succeeded, as
    `brcmf_net_attach()` does.
  - Safe: allocate the state in `ndo_init`, leave it to `priv_destructor`
    and call only `free_netdev()`, as `veth_newlink()` does for the peer
    with `veth_dev_init()` and `veth_dev_free()`.
