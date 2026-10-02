- Match key: `func`, `data` and `destroy`; each NULL argument is a wildcard;
  see `_hci_cmd_sync_lookup_entry()` in `net/bluetooth/hci_sync.c`.
- `hci_cmd_sync_lookup_entry()`: takes and drops `hdev->cmd_sync_work_lock`
  itself; in-tree callers use the result only as a boolean.
- There is no hci_cmd_sync_dequeue_once() here; code that removes one entry
  takes `hdev->cmd_sync_work_lock` and calls `_hci_cmd_sync_lookup_entry()`
  and `_hci_cmd_sync_cancel_entry()` itself.
- `_hci_cmd_sync_lookup_entry()` and `_hci_cmd_sync_cancel_entry()`: take no
  lock and assert none; the caller holds `hdev->cmd_sync_work_lock`.
- `hci_cancel_connect_sync()`: switches on `conn->type`; it does not test
  `conn->state`, and `hdev->req_status` is tested only inside
  `hci_cmd_sync_cancel()`, after the flag test.

| `conn->type` | Create in flight | Entry still queued | Neither |
|---|---|---|---|
| `ACL_LINK`, `LE_LINK` | `HCI_CONN_CREATE` set: `hci_cmd_sync_cancel()`, returns `-EBUSY` | entry cancelled with `-ECANCELED`, returns 0 | `-EBUSY` |
| `CIS_LINK` | `HCI_CONN_CREATE_CIS` set: `hci_cmd_sync_cancel()`, returns `-EBUSY` | never dequeued, `-EBUSY` | `-EBUSY` |
| other | `-ENOENT` | `-ENOENT` | `-ENOENT` |

- `HCI_CONN_CREATE`: set by `hci_acl_create_conn_sync()` and
  `hci_le_create_conn_sync()` just before the create command, cleared after
  it; the test and the cancel are under `hdev->cmd_sync_work_lock`.
- **Unsafe usage**: passing the pointer from `hci_cmd_sync_lookup_entry()` to
  `hci_cmd_sync_cancel_entry()` or dereferencing it; `hci_cmd_sync_work()` can
  unlink and `kfree()` the entry once the lock is dropped.
  - Safe: look up and cancel in one `hdev->cmd_sync_work_lock` section, as
    `hci_cmd_sync_dequeue()` does.
