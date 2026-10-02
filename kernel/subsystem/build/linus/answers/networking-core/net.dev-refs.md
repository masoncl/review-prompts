- There is no netdev_get_by_index_rcu and no __dev_get_by_flags in this
  tree.
- `netdev_get_by_flags_rcu()` in `net/core/dev.c`: caller must hold
  `rcu_read_lock()`, yet the device comes back held and tracked
  (`netdev_hold()` with `GFP_ATOMIC`); release with `netdev_put()`.
- `netdev_get_by_index_lock()`: returns with the instance lock held and no
  reference; release with `netdev_unlock()` only.
- `netdev_get_by_index_lock()` returns NULL when `reg_state` is past
  `NETREG_REGISTERED`, `moving_ns` is set, or the device is in another
  namespace; see `netdev_put_lock()`.
- `dev_hold()` with `CONFIG_NET_DEV_REFCNT_TRACKER`: counted in
  `refcnt_tracker.no_tracker`; `dev_put()` decrements the same counter.
- `netdev_tracker_alloc()`: turns an untracked reference into a tracked one
  by decrementing `no_tracker`; valid only on a reference counted there, such
  as one taken by `dev_hold()`, `dev_get_by_index()` or `dev_get_by_name()`.
- `__netdev_tracker_alloc()`: for a reference taken with `__dev_hold()`,
  which touched no tracker counter.
- **Unsafe usage**: releasing a `dev_hold()` reference with `netdev_put()` and
  a tracker, or a `netdev_hold()` reference taken with a tracker with
  `dev_put()`; with `CONFIG_NET_DEV_REFCNT_TRACKER` the `no_tracker` count is
  left unbalanced and `ref_tracker_dir_exit()` warns.
  - Safe: `dev_hold()` then `netdev_tracker_alloc()` then `netdev_put()`
    with that tracker; `netdev_get_by_index()` does the first two for its
    caller.
