- Order in `hci_unregister_dev()`:
  1. set `HCI_UNREGISTER` under `unregister_lock`
  2. `list_del()` under `write_lock(&hci_dev_list_lock)`
  3. `synchronize_srcu()`, then `cleanup_srcu_struct()`
  4. disable the work items, then `hci_devcd_shutdown()`
  5. `hci_cmd_sync_clear()`
  6. `hci_unregister_suspend_notifier()`
  7. `hci_dev_do_close()`
  8. `mgmt_index_removed()` under `hdev->lock`, then the `BUG_ON()`
  9. `hci_sock_dev_event()` with `HCI_DEV_UNREG`
  10. rfkill unregister and destroy
  11. `device_del()`, then `hci_dev_put()`
- Step 3 needs step 2: the only SRCU reader is `hci_dev_reset()`, which finds
  the device through `hci_dev_list` in `hci_dev_get_srcu()`.
- Step 5 needs step 1: `hci_cmd_sync_clear()` only cancels; the flag is what
  makes `hci_cmd_sync_submit()` return `-ENODEV`.
- Step 7 reads the flag from step 1: `hci_dev_shutdown()` skips the driver's
  `shutdown` callback, and `hci_dev_close_sync()` disables rather than
  cancels `power_off`, `ncmd_timer` and `le_scan_disable`.
- `hci_dev_close_sync()` returns before `hdev->close()` when `HCI_UP` was
  already clear, so unregistering a powered-off controller does not call
  the driver's `close`.
- Step 8 condition: `HCI_INIT`, `HCI_SETUP` and `HCI_CONFIG` all clear; user
  channel is not tested, and the `HCI_QUIRK_RAW_DEVICE` test is inside
  `mgmt_index_removed()`.
- There is no hci_del_dev_sysfs here; `hci_unregister_dev()` calls
  `device_del()` directly.
- `hci_unregister_dev()` does not remove debugfs, destroy the workqueues or
  free the index; `hci_release_dev()` does that and clears the stored lists.
- Final `hci_dev_put()`: drops the `hci_dev_hold()` taken in
  `hci_register_dev()`; the allocation reference from `device_initialize()`
  in `hci_init_sysfs()` is dropped by `hci_free_dev()`.
- `bt_host_release()` in `net/bluetooth/hci_sysfs.c`: runs on the last
  `put_device()`; with `HCI_UNREGISTER` set it calls `hci_release_dev()`,
  which ends in `kfree(hdev)`.
- `bt_host_release()` with `HCI_UNREGISTER` clear: calls
  `cleanup_srcu_struct()` and `kfree(hdev)` instead of `hci_release_dev()`;
  this is the path of a device that was never unregistered.
