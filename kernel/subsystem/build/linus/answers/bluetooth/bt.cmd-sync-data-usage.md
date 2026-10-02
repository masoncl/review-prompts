- `hci_conn_valid()`: tells whether `hci_conn_del()` has removed the
  connection from `hdev->conn_hash`; it does not keep the memory alive, the
  reference does.
- `hci_conn_del()`: calls `hci_cmd_sync_dequeue()` as its last step, after
  `hci_conn_hash_del()`, so a callback that starts later sees
  `hci_conn_valid()` fail.
- **Potentially unsafe usage**: dereferencing `conn` in a queued callback after
  `hci_conn_valid()` returned true.
  - Unsafe: when the entry holds no reference; `hci_conn_valid()` compares
    addresses only and `bt_link_release()` in `net/bluetooth/hci_sysfs.c`
    frees the object on the last `put_device()`.
  - Safe: when the entry took `hci_conn_get()` and `destroy` drops it, as
    `hci_connect_acl_sync()` with `hci_acl_create_conn_sync_complete()`.
  - Safe: for fields that `hdev->lock` protects, check and copy under
    `hci_dev_lock()`, as `hci_le_conn_rate_request_sync()` does.
- `mgmt_pending_remove()` and `mgmt_pending_free()`: do not dequeue.
- `cmd_complete_rsp()` in `net/bluetooth/mgmt.c`: calls
  `hci_cmd_sync_dequeue(match->hdev, NULL, cmd, NULL)`; it runs from
  `mgmt_index_removed()` and `__mgmt_power_off()` through
  `mgmt_pending_foreach()`.
- Other `mgmt_pending_foreach()` callbacks that remove, for example
  `settings_rsp()`: do not dequeue, so the queued callback must still
  validate.
- Validity helpers in `net/bluetooth/mgmt_util.c`:

| Helper | Lock | Effect |
|---|---|---|
| `mgmt_pending_valid()` | takes `hdev->mgmt_pending_lock` | unlinks if listed; caller then frees with `mgmt_pending_free()` |
| `mgmt_pending_listed()` | takes `hdev->mgmt_pending_lock` | tests only; stale once it returns |
| `__mgmt_pending_listed()` | asserts `hdev->mgmt_pending_lock` | tests only |

- Command from `mgmt_pending_new()`: never listed, so `mgmt_pending_valid()`
  returns false for it; `destroy` frees it for every `err`, as
  `disconnect_complete()` does.
