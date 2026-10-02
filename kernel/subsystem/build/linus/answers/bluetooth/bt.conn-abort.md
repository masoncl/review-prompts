- Second abort: `conn->abort_reason` non-zero -> return 0, nothing done; there
  is no HCI_CONN_ABORT_REQ flag. `-EEXIST` from `hci_cmd_sync_run_once()` is
  also turned into 0.
- `hci_abort_conn()` tests neither `conn->state` nor the sent command;
  `hci_cancel_connect_sync()` in `net/bluetooth/hci_sync.c` decides by link
  type, under `hdev->cmd_sync_work_lock`:

| Case | Action | Result |
|---|---|---|
| ACL/LE, `HCI_CONN_CREATE` set | `hci_cmd_sync_cancel()` | abort queued |
| ACL/LE, create entry still queued | entry cancelled | return 0 |
| CIS, `HCI_CONN_CREATE_CIS` set | `hci_cmd_sync_cancel()` | abort queued, or run inline on `cmd_sync_work` |
| anything else | none | abort queued, or run inline on `cmd_sync_work` |

- Still-queued case: `hci_abort_conn()` returns 0 without queueing
  `abort_conn_sync()` and without deleting the conn; the destroy callbacks
  only `hci_conn_put()` on `-ECANCELED`.
- Return of `hci_abort_conn()`: 0, or the queueing error (`-ENETDOWN`,
  `-ENODEV`, `-ENOMEM`); never the result of the HCI command.
- `hci_abort_conn_sync()` by `conn->state`:

| State | Command | If conn still in hash afterwards |
|---|---|---|
| `BT_CONNECTED`, `BT_CONFIG` | `hci_disconnect_sync()` | `hci_conn_failed()` |
| `BT_CONNECT` | `hci_connect_cancel_sync()` | `hci_conn_failed()` |
| `BT_CONNECT2` | `hci_reject_conn_sync()` | `hci_conn_failed()` |
| `BT_OPEN`, `BT_BOUND` | none | `hci_conn_failed()` |
| other | none | `BT_CLOSED`, `hci_disconn_cfm()`, `hci_conn_del()` |

- Own deletion does not depend on the command result: after the command it
  takes `hdev->lock` and deletes whenever
  `hci_conn_hash_lookup_handle()` on the handle saved at entry still returns
  this conn; otherwise it returns 0.
- `hci_conn_failed()` on that path notifies with `hci_connect_cfm()`, not
  `hci_disconn_cfm()`, even for `BT_CONNECTED`.
- `BIS_LINK` and `PA_LINK` in `hci_disconnect_sync()`: no command; it calls
  `hci_conn_failed()` under `hdev->lock` and returns 0.
- `hci_abort_conn_sync()` return: can be a positive HCI status (`reason` while
  `HCI_CONN_SCANNING`, `HCI_ERROR_LOCAL_HOST_TERM` for a CIS with no Create
  CIS sent).
