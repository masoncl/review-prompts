- Lock: `hdev->mgmt_pending_lock`, not `hci_dev_lock()`.
- `set_powered_sync()`: tests with `__mgmt_pending_listed()` under the
  mutex; it does not call `mgmt_pending_valid()` or `mgmt_pending_listed()`.
- `mgmt_pending_valid()` in a queued function: unlinks the command, so the
  completion callback's own `mgmt_pending_valid()` then fails and nothing
  replies or frees.
- Same pattern as `set_powered_sync()`: search `__mgmt_pending_listed` in
  `net/bluetooth/mgmt.c`; for example `set_ssp_sync()`, `set_name_sync()`
  and `set_mesh_sync()`; `mgmt_add_adv_patterns_monitor_sync()` reads
  `cmd->user_data` that way.
- `set_default_phy_sync()`: not this pattern; its command comes from
  `mgmt_pending_new()`.
- `cmd->sk`: a field of the command, so the same rule covers reading it.
- Socket reference: `mgmt_pending_new()` takes one and `mgmt_pending_free()`
  drops it; no queued function in `net/bluetooth/mgmt.c` takes its own.
- **Potentially unsafe usage**: dereferencing the command in a queued
  function outside `hdev->mgmt_pending_lock`.
  - Unsafe: for a command from `mgmt_pending_add()`, before the lock is
    taken or after it is dropped; `mgmt_pending_foreach()` with `remove`
    can free it at any time.
  - Safe: under the mutex after `__mgmt_pending_listed()` returned true,
    copying into locals, as `set_powered_sync()` does.
  - Safe: `mgmt_pending_listed()` as a go or no-go test with no later
    dereference, as `set_discoverable_sync()`, `set_connectable_sync()`,
    `start_discovery_sync()` and `stop_discovery_sync()` do.
  - Safe: for a command from `mgmt_pending_new()`; only its completion
    callback frees it, and `hci_cmd_sync_work()` runs that after the queued
    function returns, as with `get_conn_info_sync()`.
