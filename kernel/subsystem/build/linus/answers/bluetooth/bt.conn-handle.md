- Return type is `u8`, an HCI status; no negative errno.
- Checks, in order:

| Check | Return |
|---|---|
| `conn->handle == handle` | 0, before any other test |
| `handle > HCI_CONN_HANDLE_MAX` | `HCI_ERROR_INVALID_PARAMETERS` |
| `conn->abort_reason` non-zero | `conn->abort_reason` |

- No "handle already set" test and no link-type test in
  `hci_conn_set_handle()`; `hci_conn_complete_evt()`,
  `hci_sync_conn_complete_evt()` and `le_conn_complete_evt()` do
  `!HCI_CONN_HANDLE_UNSET(conn->handle)` themselves before calling it.
- No debugfs or sysfs work inside; the caller runs
  `hci_debugfs_create_conn()` and `hci_conn_add_sysfs()` itself after a 0
  return, for example `hci_conn_complete_evt()`;
  `hci_cc_le_set_cig_params()` runs neither.
- Non-zero return is not always used as the event status:
  `hci_cc_le_set_cig_params()` skips that conn;
  `hci_le_create_big_complete_evt()` forces `HCI_ERROR_UNSPECIFIED` and
  deletes it.
