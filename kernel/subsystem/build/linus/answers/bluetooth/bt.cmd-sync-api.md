| Function | Refuses when | Returns | Duplicate queued | Calls `func` directly |
|---|---|---|---|---|
| `hci_cmd_sync_submit()` | `HCI_UNREGISTER` set | `-ENODEV` | not checked | never |
| `hci_cmd_sync_queue()` | `HCI_RUNNING` clear | `-ENETDOWN` | not checked | never |
| `hci_cmd_sync_queue_once()` | `HCI_RUNNING` clear | `-ENETDOWN` | `-EEXIST` | never |
| `hci_cmd_sync_run()` | `HCI_RUNNING` clear | `-ENETDOWN` | not checked | when called on `hdev->cmd_sync_work` |
| `hci_cmd_sync_run_once()` | `HCI_RUNNING` clear | `-ENETDOWN` | `-EEXIST` | when called on `hdev->cmd_sync_work` |

- `HCI_RUNNING` is tested in `hdev->flags`, not `HCI_UP`; it is set in
  `hci_dev_open_sync()` before init, so entries are accepted during init.
- `hci_cmd_sync_submit()` makes no `HCI_RUNNING` or `HCI_UP` test and never
  calls `func`; the other four call `hci_cmd_sync_submit()` when they queue
  and can then also return `-ENODEV` or `-ENOMEM`.
- `hci_cmd_sync_run()` direct path: calls `func`, then `destroy` with the
  result of `func`, and returns 0; the caller never sees the error of `func`.
- `_once` variants: the lookup runs before the `HCI_RUNNING` test, so a
  duplicate gives `-EEXIST` even when the device is not running.
- `_once` duplicate key: `func`, `data` and `destroy` as passed; a NULL
  argument matches any value.
- `_once` variants do not see an entry that `hci_cmd_sync_work()` has already
  unlinked to run, and the lookup and the add are separate sections of
  `hdev->cmd_sync_work_lock`; a second entry can still be queued.
