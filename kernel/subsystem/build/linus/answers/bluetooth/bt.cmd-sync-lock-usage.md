- Comment in `include/net/bluetooth/hci_sync.h`: says functions with the sync
  suffix shall not be called with `hdev->lock` held; it states no exception.
- `hci_event_packet()` in `net/bluetooth/hci_event.c`: takes and drops
  `hci_dev_lock()` for every event before it dispatches, and again before it
  completes the request, so no reply is delivered while the sender holds
  `hdev->lock`, whatever the handler does.
- Callbacks that copy under `hci_dev_lock()` and unlock before sending:
  `hci_le_conn_rate_request_sync()` in `net/bluetooth/hci_sync.c`,
  `le_conn_update_sync()` in `net/bluetooth/hci_conn.c`, `conn_update_sync()`
  in `net/bluetooth/mgmt.c`.
- `le_conn_update_sync()`: retakes `hci_dev_lock()` after the command returns
  and looks the parameters up under it before it writes them.
- **Potentially unsafe usage**: calling `hci_cmd_sync_run()`,
  `hci_cmd_sync_run_once()` or `hci_abort_conn()` with `hci_dev_lock()` held.
  - Unsafe: when the caller runs on `hdev->cmd_sync_work`; `func` then runs in
    the caller and sends commands under `hdev->lock`.
  - Safe: when the caller is not on `hdev->cmd_sync_work`, so the
    `current_work()` test in `hci_cmd_sync_run()` fails and the entry is only
    queued, as `cancel_pair_device()` in `net/bluetooth/mgmt.c`.
  - Safe: on `hdev->cmd_sync_work`, take a reference under the lock and unlock
    before the call, as `disconnect_sync()` in `net/bluetooth/mgmt.c` does.
