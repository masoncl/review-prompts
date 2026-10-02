| Path that ends the entry | `err` given to `destroy` | Locks held |
|---|---|---|
| `hci_cmd_sync_work()` ran `func` | return value of `func` | `hdev->req_lock` |
| `hci_cmd_sync_run()` direct call | return value of `func` | `hdev->req_lock`, plus the caller's |
| `hci_cmd_sync_dequeue()`, `hci_cmd_sync_cancel_entry()`, `hci_cancel_connect_sync()` | `-ECANCELED` | `hdev->cmd_sync_work_lock`, plus the caller's |
| `hci_cmd_sync_clear()` | `-ECANCELED` | `hdev->cmd_sync_work_lock` |

- `hci_cmd_sync_clear()`: called only from `hci_unregister_dev()`;
  `hci_dev_close_sync()` does not call it.
- Caller's locks on the dequeue path: `hdev->lock` when `hci_conn_del()` is
  called under it, as in `hci_abort_conn_sync()`; `hdev->mgmt_pending_lock`
  when `cmd_complete_rsp()` in `net/bluetooth/mgmt.c` dequeues from inside
  `mgmt_pending_foreach()`.
- `_hci_cmd_sync_cancel_entry()`: calls `destroy` before it unlinks the entry.
- `hci_cmd_sync_run()` returning 0: `destroy` may already have run, so the
  caller no longer owns what it passed as `data`.
- No `destroy` call: when the queueing function returns `-ENODEV`, `-ENOMEM`,
  `-ENETDOWN` or `-EEXIST`; the caller frees `data` or drops its reference,
  as `hci_connect_acl_sync()` does with `hci_conn_put()`.
- **Potentially unsafe usage**: a `destroy` callback that, on `-ECANCELED`,
  takes `hci_dev_lock()` or `hdev->mgmt_pending_lock`, or calls a queueing
  function.
  - Unsafe: when `data` is a `struct hci_conn` or a listed
    `struct mgmt_pending_cmd`; `hci_conn_del()` dequeues under `hdev->lock`,
    `cmd_complete_rsp()` under `hdev->mgmt_pending_lock`, and both under
    `hdev->cmd_sync_work_lock`, which `hci_cmd_sync_submit()` and
    `hci_cmd_sync_lookup_entry()` take.
  - Safe: test `err == -ECANCELED` first and only release the data, as
    `create_le_conn_complete()` does.
  - Safe: `hci_cmd_sync_queue()` from the `destroy` of an entry whose `data`
    is NULL, as `mesh_next()` in `net/bluetooth/mgmt.c`; only
    `hci_cmd_sync_clear()` cancels such an entry, and with `HCI_UNREGISTER`
    set `hci_cmd_sync_submit()` returns before it takes
    `hdev->cmd_sync_work_lock`.
