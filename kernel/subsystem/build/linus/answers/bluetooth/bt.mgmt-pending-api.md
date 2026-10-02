- Lock: the mutex `hdev->mgmt_pending_lock`; `hci_dev_lock()` does not
  cover the list.

| Function | Lock | List and free |
|---|---|---|
| `mgmt_pending_add()` | takes the mutex | adds at tail |
| `mgmt_pending_remove()` | takes the mutex | `list_del()`, then frees |
| `mgmt_pending_find()` | takes it for the walk | none |
| `mgmt_pending_foreach()` | holds it across every callback | see below |
| `mgmt_pending_listed()` | takes the mutex | none |
| `__mgmt_pending_listed()` | `lockdep_assert_held()` | none |

- `mgmt_pending_remove()`: `list_del()` is unconditional; there is no test
  that the command is on the list.
- `mgmt_pending_foreach()` with `remove` true: unlinks before the callback
  and calls `mgmt_pending_free()` after it.
- `mgmt_pending_foreach()` callback: must not free the command, and must not
  call a helper that takes the mutex.
- `mgmt_pending_foreach()` with opcode 0: matches every command.
- `mgmt_pending_listed()` under the mutex: deadlocks; use
  `__mgmt_pending_listed()` there.
- `mgmt_pending_find()` result: not pinned once the helper returns.
- `hci_dev_lock()` does not pin a found command: completion callbacks call
  `mgmt_pending_valid()` without it, for example
  `mgmt_set_powered_complete()`.
