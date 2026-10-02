- `netif_napi_add()`, `napi_enable()`, `napi_disable()`, `netif_napi_del()`: each
  takes `netdev_lock()` (the mutex `dev->lock`) itself, so each can sleep and
  each deadlocks if the caller already holds that lock.
- `napi_enable_locked()`: can sleep only when `n->config` is set;
  `napi_restore_config()` calls `napi_set_threaded()`, which can create or
  stop the kthread.
- NAPI id and `napi_hash`: `napi_enable_locked()` assigns the id and hashes
  the instance, `napi_disable_locked()` unhashes it and leaves `napi_id` set;
  `netif_napi_add()` and `netif_napi_del()` do not touch the hash, so a new
  instance is assigned no NAPI id until it is enabled.
- `napi_hash_add()`: does nothing for an instance with
  `NAPI_STATE_NO_BUSY_POLL`, which `netif_napi_add_tx()` sets, so such an
  instance gets no id from it.
- `napi_disable_locked()`: waits in `usleep_range()`, not `msleep()`, with the
  instance lock held for the whole wait.
- `napi_enable_locked()`: has no `netdev_assert_locked()`, so lockdep does not
  catch a caller without the lock; `napi_disable_locked()`,
  `netif_napi_add_weight_locked()` and `__netif_napi_del_locked()` do assert.
- `netdev_assert_locked()`: is `lockdep_assert_held()`, see
  `include/net/netdev_lock.h`.
- `netif_napi_del()` on an enabled instance: `__netif_napi_del_locked()` hits
  `WARN_ON()` if `NAPI_STATE_SCHED` is clear, then deletes anyway.
- **Potentially unsafe usage**: `napi_enable_locked()` under a spinlock.
  - Unsafe: when the instance was added with `netif_napi_add_config()`, so
    `n->config` is set and `napi_restore_config()` may sleep.
  - Safe: when `n->config` is NULL and `netdev_lock()` was taken before the
    spinlock, as `nv_open()` in `drivers/net/ethernet/nvidia/forcedeth.c` does;
    `napi_enable_locked()` calls `napi_restore_config()` only if `n->config`.
