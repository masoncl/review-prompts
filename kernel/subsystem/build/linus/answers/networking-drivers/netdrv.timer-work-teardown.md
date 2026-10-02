- There is no del_timer_sync() or del_timer() in this tree; the names are
  `timer_delete_sync()` and `timer_delete()`.
- `timer_delete_sync_try()`: exists; returns -1 if the handler is running and
  does not wait.
- `cancel_work_sync()` and `cancel_delayed_work_sync()`: reject queueing from
  any source while they wait, then re-enable before returning; nothing blocks
  queueing afterwards.
- `disable_work_sync()` family: a depth count; each call needs its own
  `enable_work()`.
- Queueing a disabled item: returns `false` and the request is dropped.
- `timer_shutdown_sync()` in `ndo_stop`: the timer stays dead in the next
  `ndo_open`; `__mod_timer()` returns without arming until `timer_setup()`
  runs again.
- Stop/open pairing: `rtl8169_down()` calls `disable_work_sync()` and
  `rtl8169_up()` calls `enable_work()`.
- **Unsafe usage**: `cancel_work_sync()` or `timer_delete_sync()` in remove
  while the device is still registered and a callback can queue the item
  again; the handler then runs after `free_netdev()`.
  - Safe: after `unregister_netdev()` has closed the device and before
    `free_netdev()`, as `bnxt_remove_one()` does.
