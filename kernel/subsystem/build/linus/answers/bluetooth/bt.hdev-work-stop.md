| Where | Call | Work items | Later queue attempt |
|---|---|---|---|
| `hci_unregister_dev()` | `disable_work_sync()` | `rx_work`, `cmd_work`, `tx_work`, `power_on`, `error_reset` | refused |
| `hci_unregister_dev()` | `disable_delayed_work_sync()` | `cmd_timer`, `ncmd_timer` | refused |
| `hci_devcd_shutdown()` | `disable_work_sync()`, `disable_delayed_work_sync()` | `dump_rx`, `dump_timeout` of `struct hci_devcoredump` | refused |
| `hci_cmd_sync_clear()` | `cancel_work_sync()` | `cmd_sync_work`, `reenable_adv_work` | allowed |
| `hci_dev_close_sync()`, `HCI_UNREGISTER` set | `disable_delayed_work()` | `power_off`, `ncmd_timer`, `le_scan_disable` | refused; a running instance is not waited for |
| `mgmt_index_removed()`, `HCI_MGMT` set | `cancel_delayed_work_sync()` | `discov_off`, `service_cache`, `rpa_expired`, `mesh_send_done` | allowed |

- `hci_unregister_dev()` uses no `cancel_work_sync()` of its own; the
  cancels on this path are inside its callees, for example
  `hci_cmd_sync_clear()`, `hci_dev_close_sync()` and `mgmt_index_removed()`.
- `hci_devcd_shutdown()`: an empty stub without `CONFIG_DEV_COREDUMP`; see
  `include/net/bluetooth/coredump.h`.
- Refused means: `queue_work()`, `queue_delayed_work()` and
  `mod_delayed_work()` queue nothing; see `clear_pending_if_disabled()` in
  `kernel/workqueue.c`.
- Nothing calls `enable_work()` on a work item of `struct hci_dev`, so the
  disable lasts until the object is freed.
- `hci_recv_frame()` ignores the result of `queue_work()`: after the
  disable it still returns 0 while `HCI_UP` or `HCI_INIT` is set, and the
  skb waits on `rx_q` for the purge in `hci_dev_close_sync()`.
- `hci_cancel_cmd_sync()` in `net/bluetooth/hci_core.c` picks disable or
  cancel for `cmd_timer` and `ncmd_timer` by the same `HCI_UNREGISTER` test.
