- Coredump state: there is no devcd_lock; `net/bluetooth/coredump.c` takes
  `hci_dev_lock()`, for example in `hci_devcd_timeout()` and
  `hci_devcd_shutdown()`.
- `dump.supported`: cleared under the spinlock of `dump.dump_q` in
  `hci_devcd_shutdown()`, not under `hdev->lock`.
- `hdev->req_lock`: still serialises every cmd_sync entry;
  `hci_cmd_sync_work()` holds it across `entry->func` and `entry->destroy`.
- `hdev->unregister_lock`: mutex with two users; `hci_unregister_dev()` sets
  `HCI_UNREGISTER` under it, `hci_cmd_sync_submit()` tests the flag and
  queues under it.
- `hdev->mgmt_pending_lock`: mutex for the `mgmt_pending` list; see
  `net/bluetooth/mgmt_util.c`.
- `hci_cb_list_lock`: `DEFINE_MUTEX()` in `net/bluetooth/hci_core.c`.

| Outer | Inner | Seen in |
|---|---|---|
| `req_lock` | `hdev->lock` | `hci_dev_close_sync()` |
| `req_lock` | `mgmt_pending_lock` | `set_powered_sync()` |
| `hdev->lock` | `hci_cb_list_lock` | `hci_conn_hash_flush()` → `hci_disconn_cfm()` |
| `hdev->lock` | `mgmt_pending_lock` | `set_powered()` → `mgmt_pending_add()` |
| `hdev->lock` | `unregister_lock` | `set_powered()` → `hci_cmd_sync_submit()` |
| `unregister_lock` | `cmd_sync_work_lock` | `hci_cmd_sync_submit()` |
| `hdev->lock` | `cmd_sync_work_lock` | `hci_conn_del()` → `hci_cmd_sync_dequeue()` |
