- Names: there is no set_powered_complete() or set_discoverable_complete()
  here; the callbacks are `mgmt_set_powered_complete()`,
  `mgmt_set_discoverable_complete()` and `mgmt_set_connectable_complete()`.
- Callbacks whose command comes from `mgmt_pending_new()` and is never
  listed, for example: `get_conn_info_complete()`,
  `get_clock_info_complete()`, `mgmt_class_complete()`.
- Socket close: removes no pending command; `mgmt_cleanup()` handles only
  `struct mgmt_mesh_tx`.
- What unlinks a listed command: `mgmt_pending_foreach()` with `remove`,
  `mgmt_pending_remove()`, `mgmt_pending_valid()`, `remove_pairing()` and
  `remove_pairing_by_addr()`.
- `err == -ECANCELED` must be tested before `mgmt_pending_valid()`:
  `cmd_complete_rsp()` runs the callback through `hci_cmd_sync_dequeue()`
  while `mgmt_pending_foreach()` holds `hdev->mgmt_pending_lock`.
- Listed command and `-ECANCELED`: the callback returns without freeing;
  in the `cmd_complete_rsp()` case `mgmt_pending_foreach()` frees it.
- **Unsafe usage**: `mgmt_pending_remove()` after `mgmt_pending_valid()`
  returned true; the entry is already unlinked.
  - Safe: `mgmt_pending_free()`, as in `set_name_complete()`.
- **Unsafe usage**: `mgmt_pending_remove()` on a command from
  `mgmt_pending_new()`; `cmd->list` is zeroed and `list_del()` is
  unconditional.
  - Safe: `mgmt_pending_free()`, as `disconnect()` does when
    `hci_cmd_sync_queue()` fails.
  - Safe: `mgmt_pending_remove()` on a command from `mgmt_pending_add()`
    that nothing has unlinked, as `set_powered()` does under
    `hci_dev_lock()` when queueing fails.
- **Unsafe usage**: a callback for a command from `mgmt_pending_new()` that
  returns without `mgmt_pending_free()`, for any `err` including
  `-ECANCELED`; nothing else frees the command.
  - Safe: free on every path, as `disconnect_complete()` and
    `mgmt_class_complete()` do.
