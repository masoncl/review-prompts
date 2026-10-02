- Second `napi_enable()`: `napi_enable_locked()` runs `napi_restore_config()`
  or `napi_hash_add()` again before it reaches the `BUG_ON()`.
- Second `napi_enable()` while a poll is scheduled: `NAPI_STATE_SCHED` is set,
  so the `BUG_ON()` passes and the bit is cleared under the poll that owns it.
- Second `napi_disable()`: the wait is `TASK_UNINTERRUPTIBLE` and holds
  `netdev_lock()`, so a `napi_enable()` from another task blocks on the lock
  and cannot end the wait.
- `napi_disable()` on an instance that was added and never enabled: hangs the
  same way; `netif_napi_add_weight_locked()` sets the two bits the loop in
  `napi_disable_locked()` waits on.
- **Unsafe usage**: `napi_disable()` on an instance that is not enabled.
  - Safe: test a driver flag first, as `ibmvnic_napi_disable()` in
    `drivers/net/ethernet/ibm/ibmvnic.c` tests `adapter->napi_enabled`; the
    wait loop in `napi_disable_locked()` defines the requirement.
- **Unsafe usage**: `napi_enable()` on an instance that is already enabled.
  - Safe: test a driver flag first, as `ibmvnic_napi_enable()` does; the
    `BUG_ON()` in `napi_enable_locked()` defines the requirement.
